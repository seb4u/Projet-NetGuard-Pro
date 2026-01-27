from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from server.database import get_db
from server.models import Agent, Alert, Statistics
from server.auth import get_current_user
from datetime import datetime, timedelta
from io import BytesIO

# Import fpdf2 pour génération PDF
try:
    from fpdf import FPDF
except ImportError:
    FPDF = None

router = APIRouter()


@router.get("/metrics")
async def get_metrics(db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    five_min_ago = datetime.now() - timedelta(minutes=5)
    active_agents = db.query(Agent).filter(Agent.last_heartbeat > five_min_ago).count()
    total_agents = db.query(Agent).count()

    alerts_24h = db.query(Alert).filter(Alert.timestamp > datetime.now() - timedelta(hours=24)).count()
    unresolved_alerts = db.query(Alert).filter(Alert.resolved == False).count()
    critical_alerts = db.query(Alert).filter(Alert.severity == "CRITICAL", Alert.resolved == False).count()

    recent_stats = db.query(Statistics).order_by(Statistics.timestamp.desc()).first()
    alert_types = db.query(Alert.alert_type, func.count(Alert.id).label('count')).group_by(Alert.alert_type).all()

    return {
        "active_agents": active_agents,
        "total_agents": total_agents,
        "alerts_24h": alerts_24h,
        "unresolved_alerts": unresolved_alerts,
        "critical_alerts": critical_alerts,
        "total_packets": recent_stats.total_packets if recent_stats else 0,
        "packets_per_second": recent_stats.packets_per_second if recent_stats else 0,
        "alert_distribution": [{"type": t.alert_type, "count": t.count} for t in alert_types]
    }


@router.get("/traffic-stats")
async def get_traffic_stats(hours: int = 24, db: Session = Depends(get_db),
                            current_user: str = Depends(get_current_user)):
    since = datetime.now() - timedelta(hours=hours)
    stats = db.query(Statistics).filter(Statistics.timestamp > since).order_by(Statistics.timestamp.asc()).all()

    return [{
        "timestamp": s.timestamp.isoformat(),
        "packets_per_second": s.packets_per_second,
        "total_packets": s.total_packets,
        "agent_id": s.agent_id
    } for s in stats]


@router.get("/export-report")
async def export_security_report(
        db: Session = Depends(get_db),
        current_user: str = Depends(get_current_user)
):
    """
    Génère un rapport PDF de sécurité avec les métriques et alertes récentes
    """
    if FPDF is None:
        return {"error": "Module fpdf2 non installé. Exécutez: pip install fpdf2"}

    # Création du PDF
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()

    # Header style SOC
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, 297, 210, 'F')

    # Titre
    pdf.set_text_color(6, 182, 212)
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 20, 'NETGUARD PRO - RAPPORT DE SECURITE', 0, 1, 'C')

    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Genere le: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}', 0, 1, 'C')
    pdf.cell(0, 10, f'Operateur: {current_user}', 0, 1, 'C')
    pdf.ln(10)

    # Section Métriques
    pdf.set_text_color(6, 182, 212)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'METRIQUES SYSTEME', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 287, pdf.get_y())
    pdf.ln(5)

    # Récupération des données
    five_min_ago = datetime.now() - timedelta(minutes=5)
    active_agents = db.query(Agent).filter(Agent.last_heartbeat > five_min_ago).count()
    total_agents = db.query(Agent).count()
    alerts_24h = db.query(Alert).filter(Alert.timestamp > datetime.now() - timedelta(hours=24)).count()
    critical_alerts = db.query(Alert).filter(Alert.severity == "CRITICAL", Alert.resolved == False).count()

    # Tableau des métriques
    pdf.set_fill_color(30, 41, 59)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 12)

    col_width = 60
    row_height = 10

    # Headers
    pdf.cell(col_width, row_height, 'Agents Actifs', 1, 0, 'C', True)
    pdf.cell(col_width, row_height, 'Alertes 24h', 1, 0, 'C', True)
    pdf.cell(col_width, row_height, 'Critiques', 1, 0, 'C', True)
    pdf.cell(col_width, row_height, 'Statut', 1, 1, 'C', True)

    # Valeurs
    pdf.set_font('Arial', '', 12)
    pdf.cell(col_width, row_height, f'{active_agents}/{total_agents}', 1, 0, 'C')
    pdf.cell(col_width, row_height, str(alerts_24h), 1, 0, 'C')

    # Couleur selon criticité
    if critical_alerts > 0:
        pdf.set_text_color(239, 68, 68)
    pdf.cell(col_width, row_height, str(critical_alerts), 1, 0, 'C')
    pdf.set_text_color(255, 255, 255)

    status = "SECURITE COMPROMISE" if critical_alerts > 0 else "SYSTEME SECURISE"
    pdf.cell(col_width, row_height, status, 1, 1, 'C')
    pdf.ln(10)

    # Section Alertes Récentes
    pdf.set_text_color(6, 182, 212)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'ALERTES RECENTES (24h)', 0, 1, 'L')
    pdf.line(10, pdf.get_y(), 287, pdf.get_y())
    pdf.ln(5)

    # Tableau des alertes
    alerts = db.query(Alert).filter(
        Alert.timestamp > datetime.now() - timedelta(hours=24)
    ).order_by(Alert.timestamp.desc()).limit(10).all()

    if alerts:
        pdf.set_font('Arial', 'B', 10)
        pdf.set_fill_color(30, 41, 59)

        # Headers du tableau alertes
        headers = ['Heure', 'Type', 'Severite', 'Source IP', 'Cible', 'Statut']
        widths = [35, 50, 30, 45, 45, 40]

        for header, width in zip(headers, widths):
            pdf.cell(width, 8, header, 1, 0, 'C', True)
        pdf.ln()

        # Données
        pdf.set_font('Arial', '', 9)
        for alert in alerts:
            pdf.cell(35, 8, alert.timestamp.strftime('%H:%M:%S'), 1, 0, 'C')
            pdf.cell(50, 8, alert.alert_type[:20], 1, 0, 'L')

            # Couleur selon sévérité
            if alert.severity == 'CRITICAL':
                pdf.set_text_color(239, 68, 68)
            elif alert.severity == 'HIGH':
                pdf.set_text_color(249, 115, 22)
            elif alert.severity == 'MEDIUM':
                pdf.set_text_color(234, 179, 8)

            pdf.cell(30, 8, alert.severity, 1, 0, 'C')
            pdf.set_text_color(255, 255, 255)

            pdf.cell(45, 8, alert.source_ip or 'N/A', 1, 0, 'C')
            pdf.cell(45, 8, alert.target_ip or 'N/A', 1, 0, 'C')

            statut = 'RESOLU' if alert.resolved else 'ACTIF'
            pdf.cell(40, 8, statut, 1, 1, 'C')
    else:
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 10, 'Aucune alerte enregistree dans les dernieres 24 heures.', 0, 1, 'C')

    # Footer
    pdf.set_y(200)
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, 'NetGuard Pro - UVCI Master Cybersecurite & IoT - Document Confidentiel', 0, 0, 'C')

    # Génération du fichier
    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)

    filename = f"rapport_securite_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Type": "application/pdf"
        }
    )