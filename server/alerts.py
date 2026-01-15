from fastapi import APIRouter, HTTPException, Path, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import Alert

router = APIRouter()

# GET /api/alerts - Liste des alertes
@router.get("", summary="Lister toutes les alertes")
def list_alerts(db: Session = Depends(get_db)):
    return db.query(Alert).all()

# GET /api/alerts/{id} - Détail d'une alerte
@router.get("/{id}", summary="Détail d'une alerte")
def alert_detail(id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    return alert

# POST /api/alerts/{id}/acknowledge - Accuser réception
@router.post("/{id}/acknowledge", summary="Accuser réception d'une alerte")
def acknowledge_alert(id: int, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte non trouvée")
    alert.acknowledged = True
    db.commit()
    return {"message": "Alerte accusée avec succès."}
