fetch("/api/csrf-token")
    .then(response => response.json())
    .then(data => {
        document.getElementById("csrf_token").value = data.token;
        console.log("CSRF token chargé");
    })
    .catch(() => {
        console.error("Impossible de récupérer le token CSRF");
    });
