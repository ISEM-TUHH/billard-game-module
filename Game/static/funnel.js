// Fragen, Optionen und Inputfelder fÃ¼r den Funnel
const funnelQuestions = [
    {
      question: "1. Wähle den Modus aus",
      name: "mode",
      type: "radio",
      options: [
        { icon: "fa-globe", text: "Billard standortverteilt spielen", follows: "single-player-selection"}, // eventually follows: "location", when we have more than one other location
        { icon: "fa-location-dot", text: "Billard lokal spielen", follows: "player-selection"},
        { icon: "fa-wand-magic-sparkles", text: "Trickshots üben", follows: "launch"},
        { icon: "fa-clipboard", text: "Prüfungsmodus", follows: "exam-selection"}
      ]
    },
    /*{
      question: "2. Wähle den anderen Standort aus",
      name: "location",
      type: "radio",
      options: [
        { icon: "fa-people-group", text: "München" },
        { icon: "fa-users", text: "Gern in Kleingruppen, in denen man sich austauschen kann" },
        { icon: "fa-comments", text: "Der Austausch ist sehr wichtig, die Arbeit erledige ich dann effizienter allein." },
        { icon: "fa-user", text: "Am liebsten arbeite ich allein meine Aufgaben ab" }
      ]
    },*/
    {
      question: "2. Wähle deinen Spielernamen aus.",
      name: "single-player-selection",
      isAfter: "mode", // zu faul für Rückwärtssuche
      type: "selection-dynamic",
      options: "/v1/getlocalplayers",
      enter: [
        { name: "Dein Name", team: "Dein Team"}
      ]
    },
    {
      question: "2. Wählt die Spieler aus",
      name: "two-player-selection",
      type: "radio",
      options: [
        { icon: "fa-seedling", text: "Ich nutze meine Studienzeit hauptsÃ¤chlich fÃ¼r meine persÃ¶nliche Entwicklung" },
        { icon: "fa-balance-scale", text: "Studium und Freizeit stehen bei mir stets im Gleichgewicht" },
        { icon: "fa-graduation-cap", text: "Das Studium hat fÃ¼r mich die hÃ¶chste PrioritÃ¤t" }
      ]
    },
    {
      question: "2. Wähle die Prüfung aus",
      name: "exam-selection",
      type: "radio",
      isAfter: "mode",
      options: [
        { icon: "fa-robot", text: "KP II", submitTo: "./sites/kp2"},
        { icon: "fa-brain", text: "LAT", submitTo: "./sites/lat"},
        //{ icon: "fa-mountain", text: "Gute Noten standen bei mir im Vordergrund. Mit viel Engagement habe ich es zu guten Ergebnissen gebracht." },
        //{ icon: "fa-star", text: "Sehr gute Noten zu erreichen, ist mir schon immer leichtgefallen." }
      ]
    },
    {
      question: "6. Wie kÃ¶nnen wir Dich erreichen?",
      name: "kontakt",
      type: "inputs",
      fields: [
        { label: "Dein Name *", type: "text", name: "name", placeholder: "Max Mustermann" },
        { label: "Deine E-Mail-Adresse *", type: "email", name: "email", placeholder: "Max@Mustermann.de" },
        { label: "Deine Telefonnummer *", type: "tel", name: "telefon", placeholder: "+49 151 ..." }
      ]
    }
  ];
  
  let currentStep = 0;
  const collectedData = {};
  const stepsContainer = document.getElementById('funnel-steps');
  const collectedContainer = document.getElementById('collected-answers');
  const nextBtn = document.getElementById('next-btn');
  const prevBtn = document.getElementById('prev-btn');
  const submitBtn = document.getElementById('submit-btn');
  const progress = document.querySelector('#progress-bar .progress');
  
  function updateHiddenFields() {
    collectedContainer.innerHTML = '';
    for (const key in collectedData) {
      if (collectedData.hasOwnProperty(key)) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = key;
        input.value = Array.isArray(collectedData[key]) ? collectedData[key].join(', ') : collectedData[key];
        collectedContainer.appendChild(input);
      }
    }
  }
  
  function renderStep() {
    progress.style.width = ((currentStep) / funnelQuestions.length * 100) + '%';
    stepsContainer.innerHTML = '';
  
    const step = funnelQuestions[currentStep];
    const fieldset = document.createElement('fieldset');
    fieldset.style.maxWidth = '2000px';
    fieldset.style.margin = '0 auto';
    const legend = document.createElement('legend');
    legend.textContent = step.question;
    legend.style.fontSize = '1.5rem';
    legend.style.color = '#006A81';
    legend.style.marginBottom = '1rem';
    fieldset.appendChild(legend);
  
    if (step.type === 'radio' || step.type === 'checkbox') {
      const container = document.createElement('div');
      container.className = 'option-boxes';
  
      step.options.forEach(opt => {
        const label = document.createElement('label');
        label.className = 'option-box';
        const icon = document.createElement('i');
        icon.className = `fa-solid ${opt.icon}`;
        const input = document.createElement('input');
        input.type = step.type;
        input.name = step.name;
        input.value = opt.text;
  
        if (collectedData[step.name]) {
          if (step.type === 'checkbox') {
            if (collectedData[step.name].includes(opt.text)) {
              input.checked = true;
              label.classList.add('active');
            }
          } else {
            if (collectedData[step.name] === opt.text) {
              input.checked = true;
              label.classList.add('active');
            }
          }
        }
  
        label.appendChild(icon);
        label.appendChild(document.createTextNode(opt.text));
        label.appendChild(input);
  
        label.addEventListener('click', () => {
          if (step.type === 'radio') {
            // Entferne die "active"-Klasse von allen Radio-Optionen
            container.querySelectorAll('.option-box').forEach(b => b.classList.remove('active'));
            // FÃ¼ge die "active"-Klasse zur aktuellen Option hinzu
            label.classList.add('active');
            collectedData[step.name] = opt.text;
          } else if (step.type === 'checkbox') {
            if (!collectedData[step.name]) {
              collectedData[step.name] = [];
            }
            if (input.checked) {
              collectedData[step.name] = collectedData[step.name].filter(item => item !== opt.text);
              label.classList.remove('active');
              input.checked = false;
            } else {
              collectedData[step.name].push(opt.text);
              label.classList.add('active');
              input.checked = true;
            }
          }
          updateHiddenFields();
          if (opt.hasOwnProperty("follows")) {
            currentStep = funnelQuestions.findIndex(obj => obj.name === opt.follows);
            renderStep();
          } else { // assume its a final node in the funnel tree -> submit and go to site
            form = document.getElementById("funnel-form");
            form.action = opt.submitTo;
            console.log(form.action)
            form.submit();
          }
        });
        
  
        container.appendChild(label);
      });
      fieldset.appendChild(container);
    } else if (step.type === 'inputs') {
      step.fields.forEach(f => {
        const label = document.createElement('label');
        label.textContent = f.label;
        label.style.display = 'block';
        label.style.margin = '1rem 0 0.5rem';
        const input = document.createElement('input');
        input.type = f.type;
        input.name = f.name;
        input.placeholder = f.placeholder || "";
        input.required = true;
        input.style.width = '90%';
        input.style.padding = '0.5rem';
        input.style.border = '1px solid #ccc';
        input.style.borderRadius = '4px';
        if (collectedData[f.name]) {
          input.value = collectedData[f.name];
        }
        input.addEventListener('input', (e) => {
          collectedData[f.name] = e.target.value;
          updateHiddenFields();
        });
        label.appendChild(input);
        fieldset.appendChild(label);
      });
  
      /*const dsLabel = document.createElement('label');
      dsLabel.style.display = 'block';
      dsLabel.style.marginTop = '1rem';
      const dsCheckbox = document.createElement('input');
      dsCheckbox.type = 'checkbox';
      dsCheckbox.required = true;
      dsCheckbox.style.marginRight = '0.5rem';
      dsLabel.appendChild(dsCheckbox);
      dsLabel.append(' Hiermit akzeptiere ich die ');
      const dsLink = document.createElement('a');
      dsLink.href = 'https://www.tuhh.de/tuhh/datenschutz';
      dsLink.textContent = 'Datenschutzbestimmungen';
      dsLink.target = '_blank';
      dsLabel.appendChild(dsLink);
      dsLabel.append('.');
      fieldset.appendChild(dsLabel);*/
    } else if (step.type === "selection") {
      step.fields

    }
    stepsContainer.appendChild(fieldset);
    prevBtn.style.display = currentStep > 0 ? 'inline-block' : 'none';
    //nextBtn.style.display = currentStep < funnelQuestions.length - 1 ? 'inline-block' : 'none';
    submitBtn.style.display = currentStep === funnelQuestions.length - 1 ? 'inline-block' : 'none';
  }
  
  // Weiter-Button
  /*nextBtn.addEventListener('click', () => {
    const step = funnelQuestions[currentStep];
    if (
      collectedData[step.name] === undefined ||
      (Array.isArray(collectedData[step.name]) && collectedData[step.name].length === 0) ||
      collectedData[step.name] === ""
    ) {
      alert("Bitte wÃ¤hle eine Option aus oder fÃ¼lle das Feld aus.");
      return;
    }
    currentStep++; // change next step here
    step.follows
    renderStep();
  });
  */
  prevBtn.addEventListener('click', () => {
    let step = funnelQuestions[currentStep];
    currentStep = funnelQuestions.findIndex(obj => obj.name == step.isAfter);
    renderStep();
  });
  
  document.addEventListener('DOMContentLoaded', renderStep);
  
  document.getElementById("funnel-form").addEventListener("submit", async function (e) {
    e.preventDefault();
  
    const formData = new FormData(this);
  
    try {
      const response = await fetch("./sendgrid_email.php", {
        method: "POST",
        body: formData
      });
  
      const text = await response.text();
      if (text.includes("erfolgreich versendet")) {
        document.getElementById("successModal").style.display = "block";
        document.getElementById("funnel-form").reset();
        document.getElementById("funnel-steps").innerHTML = "";
        currentStep = 0;
        renderStep();
      } else {
        alert("Es gab ein Problem beim Versenden der Bewerbung. Melde' dich gern einfach per E-Mail bei Nikola.Bursac@isem-tuhh.de");
        console.log(text);
      }
    } catch (error) {
      console.error("Fehler beim Versenden des Formulars:", error);
      alert("Ein technischer Fehler ist aufgetreten. Melde' dich gern einfach per E-Mail bei Nikola.Bursac@isem-tuhh.de");
    }
  });
  