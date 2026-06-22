function copyEmailToClipboard(button) {
      const email = button.getAttribute('data-email');
      const feedback = button.nextElementSibling;

      if (!email) return;

      navigator.clipboard.writeText(email).then(() => {
        if (feedback) {
          feedback.textContent = " — Copiado!";
          button.style.display = "none";

          setTimeout(() => {
            feedback.textContent = "";
            button.style.display = "inline-block";
          }, 2500);
        }
      }).catch(err => {
        console.error("Erro ao copiar e-mail: ", err);
        feedback.textContent = " — Erro ao copiar.";
      });
    }