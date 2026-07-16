"use strict";

/* ═══════════════════════════════════════════════════════════════
   FIFA World Cup 2026 — Stadium Assistant · Front-end
   Conversational chat · Web Speech · Live telemetry · i18n
   ═══════════════════════════════════════════════════════════════ */

(function () {

  /* ─── DOM refs ─── */
  const $  = (s) => document.getElementById(s);
  const $$ = (s) => document.querySelectorAll(s);

  const form        = $("assist-form");
  const statusEl    = $("status");
  const historyEl   = $("chat-history");
  const metaEl      = $("meta");
  const submitBtn   = $("submit-btn");
  const languageSel = $("language");
  const roleSel     = $("role");
  const locInput    = $("location");
  const msgInput    = $("message");
  const micBtn      = $("mic-btn");
  const ttsToggle   = $("tts-toggle");
  const simForm     = $("simulator-form");

  const accDyslexiaBtn = $("acc-dyslexia-btn");
  const accTextBtn     = $("acc-text-btn");
  const accContrastBtn = $("acc-contrast-btn");
  const accMotionBtn   = $("acc-motion-btn");
  const heatmapToggle  = $("heatmap-toggle");
  // voiceWaveVisualizer may be absent in cached pages — guard all usages
  const voiceWaveVisualizer = $("voice-wave-visualizer") || { classList: { add: () => {}, remove: () => {} } };

  /* ─── Localisation Tables ─── */
  const L = {
    en: {
      title: "Fan Assistant", welcome: "Welcome to the FIFA World Cup 2026 venue! I can help with accessible routes, quiet zones, step-free paths, first aid, transit, and more. How can I assist you?",
      placeholder: "Ask about the venue, accessibility, food, transit…",
      alertTitle: "Active Alert:", finding: "Finding the best answer…", listening: "Listening — speak now",
      sttError: "Speech recognition error.", noSpeech: "No speech detected.",
      apiError: "Could not reach the assistant.", emptyMsg: "Please type a question.",
      toastApplied: "✓ Telemetry overrides applied", toastFailed: "✗ Failed to apply overrides",
      footer: "Demo venue data · In an emergency, contact stadium staff directly",
      // Navigation
      navDashboard: "Dashboard", navMap: "Venue Map", navStats: "Live Stats", navAlerts: "Alerts", navSettings: "Settings",
      // Header nav
      headerDashboard: "Dashboard", headerMatchStats: "Match Stats", headerVenueMap: "Venue Map", headerAssistant: "Assistant", headerEvents: "Events",
      // Status card
      liveStatus: "REAL-TIME VENUE STATUS", gateAFlow: "GATE A FLOW", gateBFlow: "GATE B FLOW",
      transitStatus: "TRANSIT STATUS", noiseLevel: "NOISE LEVEL", sensoryRoom: "SENSORY ROOM",
      // Map card
      liveMap: "LIVE VENUE MAP", heatmap: "Heatmap",
      crowdDensity: "LIVE CROWD DENSITY", congestion: "CURRENT CONGESTION", exits: "EXITS", queuePred: "QUEUE PREDICTIONS",
      accessWC: "Accessible WC", concessions: "Concessions",
      // Chat
      botName: "StadiumBOT", botSub: "How can I help you?",
      iAmA: "I am a", locationLabel: "Location", stepFree: "Step-free", quietLabel: "Quiet", audioLabel: "Audio",
      // Chips
      chipStepFree: "Step-free access", chipSensory: "Sensory room", chipFirstAid: "First Aid", chipTransit: "Transit info",
      queryStepFree: "Where is the nearest step-free entrance?",
      querySensory: "Where is the sensory quiet room?",
      queryFirstAid: "Where is the nearest first aid station?",
      queryTransit: "What is the transit status?",
      // TTS
      ttsLabel: "🔊 Read replies aloud",
      // Simulator
      simTitle: "Operations Simulator", simStaff: "Staff Only",
      simGateFlow: "Gate Crowd Flow", simElevators: "Elevators", simVenue: "Venue",
      simAlertMsg: "Alert message (optional)", simApply: "Apply Overrides",
      // Tooltip
      tooltipClickHint: "Click to ask about this area",
      tooltipStatus: "Status:",
    },
    es: {
      title: "Asistente del Estadio", welcome: "¡Bienvenido al estadio del Mundial FIFA 2026! Puedo ayudarle con rutas accesibles, zonas tranquilas, caminos sin escaleras, primeros auxilios y transporte.",
      placeholder: "Pregunte sobre instalaciones, accesibilidad, comida, tránsito…",
      alertTitle: "Alerta Activa:", finding: "Buscando la mejor respuesta…", listening: "Escuchando — hable ahora",
      sttError: "Error de reconocimiento de voz.", noSpeech: "No se detectó voz.",
      apiError: "No se pudo conectar con el asistente.", emptyMsg: "Escriba una pregunta.",
      toastApplied: "✓ Telemetría actualizada", toastFailed: "✗ Error al actualizar",
      footer: "Datos de demostración · En emergencias, contacte al personal del estadio",
      navDashboard: "Tablero", navMap: "Mapa", navStats: "En Vivo", navAlerts: "Alertas", navSettings: "Ajustes",
      headerDashboard: "Tablero", headerMatchStats: "Estadísticas", headerVenueMap: "Mapa", headerAssistant: "Asistente", headerEvents: "Eventos",
      liveStatus: "ESTADO EN TIEMPO REAL", gateAFlow: "FLUJO PUERTA A", gateBFlow: "FLUJO PUERTA B",
      transitStatus: "ESTADO TRÁNSITO", noiseLevel: "NIVEL DE RUIDO", sensoryRoom: "SALA SENSORIAL",
      liveMap: "MAPA DEL ESTADIO EN VIVO", heatmap: "Mapa de Calor",
      crowdDensity: "DENSIDAD DE MULTITUD", congestion: "CONGESTIÓN ACTUAL", exits: "SALIDAS", queuePred: "PREDICCIONES DE COLA",
      accessWC: "WC Accesible", concessions: "Concesiones",
      botName: "EstadioBot", botSub: "¿Cómo puedo ayudarle?",
      iAmA: "Soy un", locationLabel: "Ubicación", stepFree: "Sin escalones", quietLabel: "Tranquilo", audioLabel: "Audio",
      chipStepFree: "Acceso sin escalones", chipSensory: "Sala sensorial", chipFirstAid: "Primeros Auxilios", chipTransit: "Info tránsito",
      queryStepFree: "¿Dónde está la entrada sin escalones más cercana?",
      querySensory: "¿Dónde está la sala sensorial tranquila?",
      queryFirstAid: "¿Dónde está la estación de primeros auxilios más cercana?",
      queryTransit: "¿Cuál es el estado del tránsito?",
      ttsLabel: "🔊 Leer respuestas en voz alta",
      simTitle: "Simulador de Operaciones", simStaff: "Solo Personal",
      simGateFlow: "Flujo de Multitud", simElevators: "Ascensores", simVenue: "Estadio",
      simAlertMsg: "Mensaje de alerta (opcional)", simApply: "Aplicar Cambios",
      tooltipClickHint: "Haga clic para preguntar sobre esta área",
      tooltipStatus: "Estado:",
    },
    fr: {
      title: "Assistant du Stade", welcome: "Bienvenue au stade de la Coupe du Monde FIFA 2026 ! Je peux vous aider avec les itinéraires accessibles, zones calmes, chemins sans escalier, premiers secours et transports.",
      placeholder: "Posez une question sur les installations, l'accessibilité, la nourriture…",
      alertTitle: "Alerte Active :", finding: "Recherche de la meilleure réponse…", listening: "Écoute en cours — parlez",
      sttError: "Erreur de reconnaissance vocale.", noSpeech: "Aucune parole détectée.",
      apiError: "Impossible de joindre l'assistant.", emptyMsg: "Veuillez saisir une question.",
      toastApplied: "✓ Télémétrie appliquée", toastFailed: "✗ Échec de la mise à jour",
      footer: "Données de démonstration · En cas d'urgence, contactez le personnel du stade",
      navDashboard: "Tableau de Bord", navMap: "Plan du Stade", navStats: "En Direct", navAlerts: "Alertes", navSettings: "Paramètres",
      headerDashboard: "Tableau de Bord", headerMatchStats: "Stats", headerVenueMap: "Plan", headerAssistant: "Assistant", headerEvents: "Événements",
      liveStatus: "ÉTAT EN TEMPS RÉEL", gateAFlow: "FLUX PORTE A", gateBFlow: "FLUX PORTE B",
      transitStatus: "ÉTAT TRANSPORT", noiseLevel: "NIVEAU SONORE", sensoryRoom: "SALLE SENSORIELLE",
      liveMap: "PLAN DU STADE EN DIRECT", heatmap: "Carte Thermique",
      crowdDensity: "DENSITÉ DE FOULE", congestion: "CONGESTION ACTUELLE", exits: "SORTIES", queuePred: "PRÉVISIONS DE FILE",
      accessWC: "WC Accessible", concessions: "Concessions",
      botName: "StadeBot", botSub: "Comment puis-je vous aider ?",
      iAmA: "Je suis un", locationLabel: "Position", stepFree: "Sans escaliers", quietLabel: "Calme", audioLabel: "Audio",
      chipStepFree: "Accès sans escaliers", chipSensory: "Salle sensorielle", chipFirstAid: "Premiers Secours", chipTransit: "Info transport",
      queryStepFree: "Où est l'entrée sans escaliers la plus proche ?",
      querySensory: "Où est la salle sensorielle calme ?",
      queryFirstAid: "Où est le poste de premiers secours le plus proche ?",
      queryTransit: "Quel est l'état du transport ?",
      ttsLabel: "🔊 Lire les réponses à voix haute",
      simTitle: "Simulateur d'Opérations", simStaff: "Personnel Seulement",
      simGateFlow: "Flux de Foule", simElevators: "Ascenseurs", simVenue: "Stade",
      simAlertMsg: "Message d'alerte (facultatif)", simApply: "Appliquer",
      tooltipClickHint: "Cliquez pour poser une question sur cette zone",
      tooltipStatus: "Statut :",
    },
    pt: {
      title: "Assistente do Estádio", welcome: "Bem-vindo ao estádio da Copa do Mundo FIFA 2026! Posso ajudar com rotas acessíveis, zonas tranquilas, caminhos sem escadas, primeiros socorros e transporte.",
      placeholder: "Pergunte sobre instalações, acessibilidade, comida, transporte…",
      alertTitle: "Alerta Ativo:", finding: "Encontrando a melhor resposta…", listening: "Ouvindo — fale agora",
      sttError: "Erro de reconhecimento de fala.", noSpeech: "Nenhuma fala detectada.",
      apiError: "Não foi possível contatar o assistente.", emptyMsg: "Por favor, faça uma pergunta.",
      toastApplied: "✓ Telemetria aplicada", toastFailed: "✗ Falha ao aplicar",
      footer: "Dados de demonstração · Em emergências, contate o pessoal do estádio",
      navDashboard: "Painel", navMap: "Mapa do Estádio", navStats: "Ao Vivo", navAlerts: "Alertas", navSettings: "Configurações",
      headerDashboard: "Painel", headerMatchStats: "Estatísticas", headerVenueMap: "Mapa", headerAssistant: "Assistente", headerEvents: "Eventos",
      liveStatus: "STATUS EM TEMPO REAL", gateAFlow: "FLUXO PORTÃO A", gateBFlow: "FLUXO PORTÃO B",
      transitStatus: "STATUS TRANSPORTE", noiseLevel: "NÍVEL DE RUÍDO", sensoryRoom: "SALA SENSORIAL",
      liveMap: "MAPA DO ESTÁDIO AO VIVO", heatmap: "Mapa de Calor",
      crowdDensity: "DENSIDADE DA MULTIDÃO", congestion: "CONGESTIONAMENTO ATUAL", exits: "SAÍDAS", queuePred: "PREVISÃO DE FILAS",
      accessWC: "WC Acessível", concessions: "Lanchonetes",
      botName: "EstádioBot", botSub: "Como posso ajudar?",
      iAmA: "Eu sou um", locationLabel: "Localização", stepFree: "Sem escadas", quietLabel: "Silencioso", audioLabel: "Áudio",
      chipStepFree: "Acesso sem escadas", chipSensory: "Sala sensorial", chipFirstAid: "Primeiros Socorros", chipTransit: "Info transporte",
      queryStepFree: "Onde fica a entrada sem escadas mais próxima?",
      querySensory: "Onde fica a sala sensorial tranquila?",
      queryFirstAid: "Onde fica o posto de primeiros socorros mais próximo?",
      queryTransit: "Qual é o status do transporte?",
      ttsLabel: "🔊 Ler respostas em voz alta",
      simTitle: "Simulador de Operações", simStaff: "Somente Pessoal",
      simGateFlow: "Fluxo de Multidão", simElevators: "Elevadores", simVenue: "Estádio",
      simAlertMsg: "Mensagem de alerta (opcional)", simApply: "Aplicar Alterações",
      tooltipClickHint: "Clique para perguntar sobre esta área",
      tooltipStatus: "Status:",
    },
    de: {
      title: "Stadion-Assistent", welcome: "Willkommen im FIFA Weltmeisterschaft 2026 Stadion! Ich kann Ihnen mit barrierefreien Wegen, ruhigen Zonen, stufenfreien Pfaden, Erste Hilfe und Transit helfen.",
      placeholder: "Fragen zu Einrichtungen, Barrierefreiheit, Essen, Transit…",
      alertTitle: "Aktive Warnung:", finding: "Beste Antwort wird gesucht…", listening: "Höre zu — bitte sprechen",
      sttError: "Spracherkennungsfehler.", noSpeech: "Keine Sprache erkannt.",
      apiError: "Assistent nicht erreichbar.", emptyMsg: "Bitte eine Frage eingeben.",
      toastApplied: "✓ Telemetrie übernommen", toastFailed: "✗ Fehler beim Übernehmen",
      footer: "Demo-Daten · Im Notfall wenden Sie sich an das Stadionpersonal",
      navDashboard: "Übersicht", navMap: "Stadionkarte", navStats: "Live-Daten", navAlerts: "Hinweise", navSettings: "Einstellungen",
      headerDashboard: "Übersicht", headerMatchStats: "Spielstatistik", headerVenueMap: "Stadionkarte", headerAssistant: "Assistent", headerEvents: "Veranstaltungen",
      liveStatus: "ECHTZEIT-STADIONZUSTAND", gateAFlow: "TOR A DURCHFLUSS", gateBFlow: "TOR B DURCHFLUSS",
      transitStatus: "NAHVERKEHR", noiseLevel: "LÄRMPEGEL", sensoryRoom: "RUHEZONE",
      liveMap: "LIVE STADIONKARTE", heatmap: "Heatmap",
      crowdDensity: "LIVE MENSCHENMENGE", congestion: "AKTUELLE STAUUNG", exits: "AUSGÄNGE", queuePred: "WARTEZEIT-PROGNOSE",
      accessWC: "Barrierefreie WC", concessions: "Verkaufsstände",
      botName: "StadionBot", botSub: "Wie kann ich helfen?",
      iAmA: "Ich bin ein", locationLabel: "Standort", stepFree: "Stufenfrei", quietLabel: "Ruhig", audioLabel: "Audio",
      chipStepFree: "Stufenfreier Zugang", chipSensory: "Ruhezone", chipFirstAid: "Erste Hilfe", chipTransit: "Nahverkehr-Info",
      queryStepFree: "Wo ist der nächste stufenfreie Eingang?",
      querySensory: "Wo ist der ruhige Sinnesraum?",
      queryFirstAid: "Wo ist die nächste Erste-Hilfe-Station?",
      queryTransit: "Wie ist der Nahverkehrsstatus?",
      ttsLabel: "🔊 Antworten vorlesen",
      simTitle: "Betriebs-Simulator", simStaff: "Nur Personal",
      simGateFlow: "Tor-Personenstrom", simElevators: "Aufzüge", simVenue: "Stadion",
      simAlertMsg: "Warnmeldung (optional)", simApply: "Übernehmen",
      tooltipClickHint: "Klicken, um über diesen Bereich zu fragen",
      tooltipStatus: "Status:",
    },
  };

  /* ─── i18n JSON Cache ─── */
  const _translationCache = {};

  /**
   * Load translations for `lang` from the served JSON files.
   * Falls back to English for any missing key.
   * Logs a console.warn for every missing key in non-English locales.
   *
   * @param {string} lang - BCP-47 language code.
   * @returns {Promise<object>} Resolved translation map.
   */
  async function loadTranslations(lang) {
    if (_translationCache[lang]) return _translationCache[lang];
    try {
      const res = await fetch(`/static/i18n/${lang}.json`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      _translationCache[lang] = data;
      return data;
    } catch (err) {
      console.warn(`[i18n] Failed to load '${lang}', falling back to 'en':`, err);
      if (lang !== "en") return loadTranslations("en");
      return {};
    }
  }

  /**
   * Return the translation string for `key` from the in-memory L table
   * (used synchronously during page load before JSON is ready).
   *
   * @param {string} key
   * @returns {string}
   */
  function t(key) {
    const cur = languageSel.value || "en";
    return (L[cur] || L.en)[key] || L.en[key] || key;
  }

  /* ─── Toast Notifications ─── */
  function toast(message, type) {
    const el = document.createElement("div");
    el.className = `toast ${type || "success"}`;
    el.textContent = message;
    $("toast-container").appendChild(el);
    setTimeout(() => el.remove(), 3200);
  }

  /* ─── UI Translation ─── */
  /**
   * Apply translations to all `[data-i18n]`, `[data-i18n-placeholder]`,
   * `[data-i18n-aria-label]`, and `[data-i18n-title]` elements from the
   * loaded JSON cache. Falls back to the synchronous `t()` table when the
   * JSON for the current language has not yet been loaded.
   *
   * Also updates `<html lang>` so AT announces the correct language.
   */
  async function translateUI() {
    const lang = languageSel.value || "en";
    document.documentElement.lang = lang;
    const tr = await loadTranslations(lang);
    const fallback = L[lang] || L.en;

    function resolve(key) {
      const val = tr[key] || fallback[key] || L.en[key];
      if (!val) console.warn(`[i18n] missing key '${key}' for lang '${lang}'`);
      return val || key;
    }

    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.dataset.i18n;
      el.textContent = resolve(key);
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      el.placeholder = resolve(el.dataset.i18nPlaceholder);
    });
    document.querySelectorAll("[data-i18n-aria-label]").forEach(el => {
      el.setAttribute("aria-label", resolve(el.dataset.i18nAriaLabel));
    });
    document.querySelectorAll("[data-i18n-title]").forEach(el => {
      el.title = resolve(el.dataset.i18nTitle);
    });

    // Keep alert title in sync (injected dynamically)
    const alertTitle = $("alert-title");
    if (alertTitle) alertTitle.textContent = resolve("alertTitle");
    // Persist selected language across page refreshes
    try { sessionStorage.setItem("stadium-lang", lang); } catch { /* non-critical */ }
  }

  /* ─── Language selector ─── */
  fetch("/languages")
    .then(r => r.ok ? r.json() : null)
    .then(async (data) => {
      if (!data?.languages) return;
      languageSel.innerHTML = "";
      for (const [code, name] of Object.entries(data.languages)) {
        const opt = document.createElement("option");
        opt.value = code; opt.textContent = name;
        languageSel.appendChild(opt);
      }
      // Restore previously-chosen language, falling back to "en".
      // Setting this AFTER populating options avoids the race where
      // languageSel.value = "en" fires before options exist.
      let restored = "en";
      try { restored = sessionStorage.getItem("stadium-lang") || "en"; } catch { /* non-critical */ }
      languageSel.value = languageSel.querySelector(`option[value="${restored}"]`) ? restored : "en";
      await translateUI();
    })
    .catch(err => { console.error("fetch /languages failed", err); });

  languageSel.addEventListener("change", () => {
    translateUI();
    connectSSE();
  });

  /* ─── Role badge sync ─── */
  if (roleSel) {
    roleSel.addEventListener("change", () => {
      const badge = $("current-role-badge");
      if (badge) badge.textContent = roleSel.options[roleSel.selectedIndex].text;
    });
  }

  /* ─── Floating mic button ─── */
  const floatingMicBtn = $("floating-mic-btn");
  if (floatingMicBtn && micBtn) {
    floatingMicBtn.addEventListener("click", () => micBtn.click());
  }

  /* ─── Settings Button (Simulator Toggle) ─── */
  const navSettings = $("nav-settings");
  if (navSettings) {
    navSettings.addEventListener("click", () => {
      const panel = $("simulator-panel");
      if (panel) panel.hidden = !panel.hidden;
    });
  }

  /* ─── Accessibility Panel Handlers ─── */
  if (accDyslexiaBtn) {
    accDyslexiaBtn.addEventListener("click", () => {
      const active = document.body.classList.toggle("dyslexia-mode");
      accDyslexiaBtn.classList.toggle("active", active);
      accDyslexiaBtn.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  if (accTextBtn) {
    accTextBtn.addEventListener("click", () => {
      const active = document.body.classList.toggle("large-text-mode");
      accTextBtn.classList.toggle("active", active);
      accTextBtn.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  if (accContrastBtn) {
    accContrastBtn.addEventListener("click", () => {
      const active = document.body.classList.toggle("high-contrast-mode");
      accContrastBtn.classList.toggle("active", active);
      accContrastBtn.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  if (accMotionBtn) {
    accMotionBtn.addEventListener("click", () => {
      const active = document.body.classList.toggle("reduced-motion");
      accMotionBtn.classList.toggle("active", active);
      accMotionBtn.setAttribute("aria-pressed", active ? "true" : "false");
    });
  }

  /* ─── Heatmap Toggle Handler ─── */
  if (heatmapToggle) {
    heatmapToggle.addEventListener("change", () => {
      const svg = $("stadium-svg");
      if (svg) svg.classList.toggle("heatmap-active", heatmapToggle.checked);
    });
  }

  /* ─── Helpers ─── */
  function selectedNeeds() {
    return Array.from($$('input[name="need"]:checked')).map(el => el.value);
  }

  function setStatus(text, isError) {
    statusEl.textContent = text;
    statusEl.classList.toggle("error", Boolean(isError));
    // Screen readers interrupt for errors (assertive); normal status is polite.
    statusEl.setAttribute("aria-live", isError ? "assertive" : "polite");
  }


  /* ─── Text-to-Speech ─── */
  /** BCP-47 codes for each supported UI language. */
  const BCP47 = { en: "en-US", es: "es-ES", fr: "fr-FR", pt: "pt-BR", de: "de-DE" };

  function speak(text, lang) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const clean = text.replace(/-\s+/g, " ").replace(/\(.*?\)/g, "").trim();
    const u = new SpeechSynthesisUtterance(clean);
    u.lang = BCP47[lang] || "en-US";
    window.speechSynthesis.speak(u);
  }

  /* ─── Speech-to-Text ─── */
  const STT = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recog = null, listening = false;

  if (STT) {
    recog = new STT();
    recog.continuous = false;
    recog.interimResults = false;
    recog.onstart  = () => { 
      listening = true;  
      micBtn.classList.add("recording"); 
      voiceWaveVisualizer.classList.add("active");
      setStatus(t("listening"), false); 
    };
    recog.onresult = (e) => { msgInput.value = e.results[0][0].transcript; setStatus("", false); form.dispatchEvent(new Event("submit")); };
    recog.onerror  = () => { 
      setStatus(t("sttError"), true); 
      micBtn.classList.remove("recording"); 
      voiceWaveVisualizer.classList.remove("active");
      listening = false; 
    };
    recog.onend    = () => { 
      micBtn.classList.remove("recording"); 
      voiceWaveVisualizer.classList.remove("active");
      listening = false; 
    };
  } else {
    micBtn.style.display = "none";
  }

  micBtn.addEventListener("click", () => {
    if (!recog) return;
    if (listening) { recog.stop(); return; }
    recog.lang = BCP47[languageSel.value] || "en-US";
    recog.start();
  });

  /* ─── Auto-resize textarea ─── */
  msgInput.addEventListener("input", () => {
    msgInput.style.height = "auto";
    msgInput.style.height = Math.min(msgInput.scrollHeight, 120) + "px";
  });

  /* ─── Chat Rendering ─── */
  function appendMsg(sender, text) {
    const wrapper = document.createElement("div");
    wrapper.className = `chat-bubble ${sender === "user" ? "user" : "assistant"}`;

    const avatar = document.createElement("div");
    avatar.className = "bubble-avatar";
    avatar.textContent = sender === "assistant" ? "✦" : "F";

    const body = document.createElement("div");
    body.className = "bubble-text";

    // Render bulleted lines as a list, plain text as paragraphs
    const lines = text.split("\n");
    let ul = null;
    lines.forEach(line => {
      const trimmed = line.trim();
      if (trimmed.startsWith("- ")) {
        if (!ul) { ul = document.createElement("ul"); ul.style.cssText = "margin:.3em 0;padding-left:1.2em;"; }
        const li = document.createElement("li");
        li.textContent = trimmed.slice(2);
        ul.appendChild(li);
      } else {
        if (ul) { body.appendChild(ul); ul = null; }
        if (trimmed) {
          const p = document.createElement("p");
          p.textContent = trimmed;
          p.style.margin = "0 0 .3em";
          body.appendChild(p);
        }
      }
    });
    if (ul) body.appendChild(ul);

    wrapper.appendChild(avatar);
    wrapper.appendChild(body);

    historyEl.appendChild(wrapper);
    historyEl.scrollTop = historyEl.scrollHeight;
    return wrapper;
  }

  function appendTyping() {
    const wrapper = document.createElement("div");
    wrapper.className = "chat-bubble assistant";
    const av = document.createElement("div"); av.className = "bubble-avatar"; av.textContent = "✦";
    const dots = document.createElement("div"); dots.className = "bubble-text typing-dots";
    dots.innerHTML = "<span></span><span></span><span></span>";
    wrapper.appendChild(av); wrapper.appendChild(dots);
    historyEl.appendChild(wrapper);
    historyEl.scrollTop = historyEl.scrollHeight;
    return wrapper;
  }

  /* ─── Submit Query (streaming) ─── */
  async function submitQuery(query) {
    const lang = languageSel.value;
    appendMsg("user", query);
    const typing = appendTyping();

    submitBtn.setAttribute("aria-busy", "true");
    submitBtn.disabled = true;
    setStatus(t("finding"), false);
    metaEl.hidden = true;

    const payload = {
      message: query, language: lang, role: roleSel.value,
      accessibility_needs: selectedNeeds(),
      location: locInput.value.trim() || null,
    };

    // Streaming is available in all modern browsers (Chrome 43+, FF 65+, Safari 14.1+)
    const canStream = typeof ReadableStream !== "undefined";

    if (canStream) {
      try {
        const res = await fetch("/api/assist/stream", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok || !res.body) throw new Error("Stream not available");

        // Build the streaming bubble (replaces the typing indicator)
        typing.remove();
        const wrapper = document.createElement("div");
        wrapper.className = "chat-bubble assistant";
        const av = document.createElement("div"); av.className = "bubble-avatar"; av.textContent = "✦";
        const bodyEl = document.createElement("div"); bodyEl.className = "bubble-text";
        wrapper.appendChild(av); wrapper.appendChild(bodyEl);
        historyEl.appendChild(wrapper);
        historyEl.scrollTop = historyEl.scrollHeight;

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        let finalData = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });

          // Parse SSE lines from the buffer
          const lines = buf.split("\n");
          buf = lines.pop(); // keep incomplete line in buf
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            const raw = line.slice(6);
            try {
              const ev = JSON.parse(raw);
              if (ev.token !== undefined) {
                bodyEl.textContent += ev.token;
                historyEl.scrollTop = historyEl.scrollHeight;
              } else if (ev.done) {
                finalData = ev;
              } else if (ev.error) {
                setStatus(ev.error, true);
              }
            } catch { /* malformed chunk */ }
          }
        }

        setStatus("", false);
        if (finalData) {
          if (ttsToggle.checked) speak(finalData.reply || bodyEl.textContent, lang);
          const bits = [`Topic: ${finalData.intent}`];
          bits.push(finalData.used_llm ? "AI-generated" : "offline guide");
          if (finalData.cache_hit) bits.push("⚡ cached");
          if (finalData.injection_suspected) bits.push("safety check applied");
          metaEl.textContent = bits.join(" · ");
          metaEl.hidden = false;
        }
      } catch (err) {
        console.warn("Streaming failed, falling back to non-streaming:", err);
        typing.remove();
        // Fall through to non-streaming below
        await _submitNonStreaming(payload, lang);
      } finally {
        submitBtn.removeAttribute("aria-busy");
        submitBtn.disabled = false;
      }
      return;
    }

    // ── Non-streaming fallback ──────────────────────────────────────────────
    await _submitNonStreaming(payload, lang);
    typing.remove();
    submitBtn.removeAttribute("aria-busy");
    submitBtn.disabled = false;
  }

  async function _submitNonStreaming(payload, lang) {
    try {
      const res = await fetch("/api/assist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(err => { console.error("API response JSON parse failed", err); return {}; });

      if (!res.ok) { setStatus(data.detail || t("apiError"), true); return; }

      setStatus("", false);
      appendMsg("assistant", data.reply || "");

      if (ttsToggle.checked) speak(data.reply || "", lang);

      const bits = [`Topic: ${data.intent}`];
      bits.push(data.used_llm ? "AI-generated" : "offline guide");
      if (data.cache_hit) bits.push("⚡ cached");
      if (data.injection_suspected) bits.push("safety check applied");
      metaEl.textContent = bits.join(" · ");
      metaEl.hidden = false;
    } catch (err) {
      console.error("submitQuery failed", err);
      setStatus(t("apiError"), true);
    }
  }

  /* ─── Form Submit ─── */
  form.addEventListener("submit", e => {
    e.preventDefault();
    const q = msgInput.value.trim();
    if (!q) { setStatus(t("emptyMsg"), true); return; }
    msgInput.value = "";
    msgInput.style.height = "auto";
    submitQuery(q);
  });

  /* ─── Quick Chips ─── */
  $$(".chip").forEach(chip => {
    chip.addEventListener("click", () => submitQuery(chip.dataset.query));
  });

  /* ─── Map Interactions ─── */
  const mapQueries = {
    "map-node-gateA":  { loc: "Gate A",       q: "How do I get in through Gate A using step-free access?" },
    "map-node-gateB":  { loc: "Gate B",       q: "What is the status of Gate B and its elevator?" },
    "map-node-gateC":  { loc: "Gate C",       q: "How do I reach Gate C?" },
    "map-node-gateD":  { loc: "Gate D",       q: "Is Gate D accessible?" },
    "map-node-transit": { loc: "Transit Hub",  q: "What is the transit status and how do I get to the trains?" },
    "map-node-sec108": { loc: "Section 108",  q: "Where are the accessible restrooms near Section 108?" },
    "map-node-sec112": { loc: "Section 112",  q: "Where is the quiet sensory room?" },
    "map-node-sec104": { loc: "Section 104",  q: "Where is the nearest first aid station?" },
    "map-node-sec118": { loc: "Section 118",  q: "Where is the family room?" },
    "map-node-water":  { loc: "Pitch Center", q: "Where can I refill water and recycle?" },
  };

  for (const [id, info] of Object.entries(mapQueries)) {
    const el = $(id);
    if (!el) continue;
    const handler = () => { locInput.value = info.loc; submitQuery(info.q); };
    el.addEventListener("click", handler);
    el.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); handler(); } });
  }

  /* ─── Telemetry Rendering ─── */
  function setElementClass(el, className) {
    if (!el) return;
    if (typeof el.className === "string") {
      el.className = className;
      return;
    }
    if (typeof el.setAttribute === "function") {
      el.setAttribute("class", className);
    }
  }

  function badgeClass(level) {
    if (level === "High" || level === "Offline" || level === "Major Delays" || level === "Full") return "red";
    if (level === "Medium" || level === "Minor Delays" || level === "Near Capacity" || level === "Busy") return "yellow";
    return "green";
  }

  function renderTelemetry(s) {
    const gates = ["A", "B", "C", "D"];

    // Heatmap classes mapping helper
    function heatmapClass(level) {
      if (level === "High") return "heatmap-glow-circle high high-pulse";
      if (level === "Medium") return "heatmap-glow-circle med med-pulse";
      return "heatmap-glow-circle low low-pulse";
    }

    function nodeCongestClass(level) {
      if (level === "High") return "high-congest";
      if (level === "Medium") return "med-congest";
      return "low-congest";
    }

    // ── Update new match stats banner ──
    const gA = s.gate_congestion?.A || "Low";
    const gB = s.gate_congestion?.B || "Low";
    const tr = s.transit_status || "On Time";
    const sr = s.sensory_room_occupancy || "Open";

    const statGateA = $("stat-gateA"); if (statGateA) { statGateA.textContent = gA.toUpperCase(); setElementClass(statGateA, `metric-value ${gA==="High"?"red-text":gA==="Medium"?"amber":"teal"}`); }
    const statGateB = $("stat-gateB"); if (statGateB) { statGateB.textContent = gB.toUpperCase(); setElementClass(statGateB, `metric-value ${gB==="High"?"red-text":gB==="Medium"?"amber":"teal"}`); }
    const statTransit = $("stat-transit"); if (statTransit) { statTransit.textContent = tr.toUpperCase(); setElementClass(statTransit, `metric-value ${tr.includes("Major")?"red-text":tr.includes("Minor")?"amber":"teal"}`); }
    const statSensory = $("stat-sensory"); if (statSensory) { statSensory.textContent = sr.toUpperCase(); setElementClass(statSensory, `metric-value ${sr==="Full"?"red-text":sr==="Near Capacity"?"amber":"teal"}`); }

    // Update legend
    const legA = $("leg-gateA"); if (legA) { legA.textContent = gA; setElementClass(legA, `cong-val ${gA==="High"?"red-text":gA==="Medium"?"amber-text":"teal-text"}`); }
    const legB = $("leg-gateB"); if (legB) { legB.textContent = gB; setElementClass(legB, `cong-val ${gB==="High"?"red-text":gB==="Medium"?"amber-text":"teal-text"}`); }
    const legTr = $("leg-transit"); if (legTr) { legTr.textContent = tr; setElementClass(legTr, `cong-val ${tr.includes("Major")?"red-text":tr.includes("Minor")?"amber-text":"teal-text"}`); }

    // Queue widget
    const qWc = $("q-wc"); const qWcTime = $("q-wc-time");
    const qCon = $("q-con"); const qConTime = $("q-con-time");
    if (qWc) {
      if (gA==="High"||gB==="High") { qWc.style.width="80%"; if(qWcTime) qWcTime.textContent="~15 min"; setElementClass(qWc,"queue-bar-fill amber-fill"); }
      else if (gA==="Medium"||gB==="Medium") { qWc.style.width="40%"; if(qWcTime) qWcTime.textContent="~8 min"; setElementClass(qWc,"queue-bar-fill"); }
      else { qWc.style.width="15%"; if(qWcTime) qWcTime.textContent="~3 min"; setElementClass(qWc,"queue-bar-fill"); }
    }
    if (qCon) {
      if (gA==="High"&&gB==="High") { qCon.style.width="90%"; if(qConTime) qConTime.textContent="~20 min"; setElementClass(qCon,"queue-bar-fill amber-fill"); }
      else if (gA==="Medium"||gB==="Medium") { qCon.style.width="55%"; if(qConTime) qConTime.textContent="~12 min"; setElementClass(qCon,"queue-bar-fill amber-fill"); }
      else { qCon.style.width="20%"; if(qConTime) qConTime.textContent="~4 min"; setElementClass(qCon,"queue-bar-fill"); }
    }


    gates.forEach(g => {
      const cl = s.gate_congestion[g] || "Low";
      const b = $(`tel-gate${g}-congest`);
      if (b) { b.textContent = cl; setElementClass(b, `badge ${badgeClass(cl)}`); }
      const d = $(`map-dot-gate${g}`);
      if (d) setElementClass(d, `dot ${badgeClass(cl)}`);

      // Heatmap circle updates
      const hCircle = $(`heatmap-circle-gate${g}`);
      if (hCircle) hCircle.setAttribute("class", heatmapClass(cl));
      const mNode = $(`map-node-gate${g}`);
      if (mNode) {
        mNode.classList.remove("high-congest", "med-congest", "low-congest");
        mNode.classList.add(nodeCongestClass(cl));
      }
    });

    gates.forEach(g => {
      const st = s.elevator_status[g] || "Online";
      const b = $(`tel-gate${g}-elev`);
      if (b) { b.textContent = st; setElementClass(b, `badge ${badgeClass(st)}`); }
      const node = $(`map-node-gate${g}`);
      if (node) node.classList.toggle("warning", st === "Offline");
    });

    // Transit
    const trEl = $("tel-transit-summary");
    if (trEl) { trEl.textContent = tr; setElementClass(trEl, `tel-big ${badgeClass(tr)}-text`); }
    const trDot = $("map-dot-transit");
    if (trDot) setElementClass(trDot, `dot ${badgeClass(tr)}`);
    const trTxt = $("map-text-transit");
    if (trTxt) {
      trTxt.textContent = tr;
      setElementClass(trTxt, `node-value ${badgeClass(tr) === "green" ? "ok" : badgeClass(tr) === "yellow" ? "warn" : "bad"}`);
    }

    const trH = $(`heatmap-circle-transit`);
    if (trH) {
      const trLevel = tr === "Major Delays" ? "High" : tr === "Minor Delays" ? "Medium" : "Low";
      trH.setAttribute("class", heatmapClass(trLevel));
      const trNode = $("map-node-transit");
      if (trNode) {
        trNode.classList.remove("high-congest", "med-congest", "low-congest");
        trNode.classList.add(nodeCongestClass(trLevel));
      }
    }

    // Sensory
    const srEl = $("tel-sensory-summary");
    if (srEl) { srEl.textContent = sr; setElementClass(srEl, `tel-big ${badgeClass(sr)}-text`); }

    const srH = $(`heatmap-circle-sec112`);
    if (srH) {
      const srLevel = sr === "Full" ? "High" : sr === "Near Capacity" ? "Medium" : "Low";
      srH.setAttribute("class", heatmapClass(srLevel));
      const srNode = $("map-node-sec112");
      if (srNode) {
        srNode.classList.remove("high-congest", "med-congest", "low-congest");
        srNode.classList.add(nodeCongestClass(srLevel));
      }
    }

    // Dynamic restroom calculation based on average Gate congestion
    let busyCount = 0;
    gates.forEach(g => { if (s.gate_congestion[g] === "High") busyCount += 2; else if (s.gate_congestion[g] === "Medium") busyCount += 1; });
    const restLevel = busyCount >= 5 ? "High" : busyCount >= 2 ? "Medium" : "Low";
    const restH = $(`heatmap-circle-sec108`);
    if (restH) {
      restH.setAttribute("class", heatmapClass(restLevel));
      const restNode = $("map-node-sec108");
      if (restNode) {
        restNode.classList.remove("high-congest", "med-congest", "low-congest");
        restNode.classList.add(nodeCongestClass(restLevel));
      }
    }

    // Queue updates
    const qRestVal = $("queue-val-restroom");
    const qRestFill = $("queue-fill-restroom");
    if (qRestVal && qRestFill) {
      if (restLevel === "High") {
        qRestVal.textContent = "12 mins";
        qRestFill.style.width = "85%";
        setElementClass(qRestFill, "queue-status-fill red");
      } else if (restLevel === "Medium") {
        qRestVal.textContent = "6 mins";
        qRestFill.style.width = "45%";
        setElementClass(qRestFill, "queue-status-fill yellow");
      } else {
        qRestVal.textContent = "2 mins";
        qRestFill.style.width = "15%";
        setElementClass(qRestFill, "queue-status-fill green");
      }
    }

    const qSensVal = $("queue-val-sensory");
    const qSensFill = $("queue-fill-sensory");
    if (qSensVal && qSensFill) {
      if (sr === "Full") {
        qSensVal.textContent = "Full (20+m)";
        qSensFill.style.width = "95%";
        setElementClass(qSensFill, "queue-status-fill red");
      } else if (sr === "Near Capacity") {
        qSensVal.textContent = "Near Cap (8m)";
        qSensFill.style.width = "65%";
        setElementClass(qSensFill, "queue-status-fill yellow");
      } else {
        qSensVal.textContent = "No Wait";
        qSensFill.style.width = "10%";
        setElementClass(qSensFill, "queue-status-fill green");
      }
    }

    // Concessions queue predictions
    const qConVal = $("queue-val-concessions");
    const qConFill = $("queue-fill-concessions");
    if (qConVal && qConFill) {
      // average dynamic wait based on gate flows
      if (busyCount >= 6) {
        qConVal.textContent = "18 mins";
        qConFill.style.width = "90%";
        setElementClass(qConFill, "queue-status-fill red");
      } else if (busyCount >= 3) {
        qConVal.textContent = "9 mins";
        qConFill.style.width = "50%";
        setElementClass(qConFill, "queue-status-fill yellow");
      } else {
        qConVal.textContent = "3 mins";
        qConFill.style.width = "20%";
        setElementClass(qConFill, "queue-status-fill green");
      }
    }

    // Alert
    const alertBox = $("active-alert-box");
    if (s.active_alert) {
      $("alert-desc").textContent = s.active_alert;
      alertBox.hidden = false;
    } else {
      alertBox.hidden = true;
    }
  }

  /* ─── Fetch Telemetry ─── */
  async function fetchStatus() {
    try {
      const res = await fetch("/api/stadium/status");
      if (!res.ok) return;
      const data = await res.json();
      renderTelemetry(data);
      syncSimulator(data);
    } catch (err) {
      console.error("fetchStatus failed", err);
    }
  }

  function syncSimulator(data) {
    ["A","B","C","D"].forEach(g => {
      const cSel = $(`sim-gate${g}`); if (cSel) cSel.value = data.gate_congestion[g];
      const eSel = $(`sim-elev${g}`); if (eSel) eSel.value = data.elevator_status[g];
    });
    const simTr = $("sim-transit"); if (simTr) simTr.value = data.transit_status;
    const simSr = $("sim-sensory"); if (simSr) simSr.value = data.sensory_room_occupancy;
    const simAl = $("sim-alert");   if (simAl) simAl.value = data.active_alert || "";
  }

  let sseSource = null;
  let pollingTimer = null;

  function connectSSE() {
    if (sseSource) {
      sseSource.close();
    }
    const needs = selectedNeeds().join(",");
    const role = roleSel.value;
    const lang = languageSel.value;
    const loc = encodeURIComponent(locInput.value.trim() || "");

    const url = `/api/stadium/stream?needs=${needs}&role=${role}&lang=${lang}&location=${loc}`;
    sseSource = new EventSource(url);

    sseSource.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        renderTelemetry(data);
        syncSimulator(data);
      } catch (err) {
        console.error("Failed to parse SSE data", err);
      }
    };

    sseSource.onerror = (err) => {
      console.warn("SSE error, falling back to polling in 5s", err);
      sseSource.close();
      sseSource = null;
      if (!pollingTimer) {
        pollingTimer = setInterval(fetchStatus, 6000);
      }
    };

    sseSource.onopen = () => {
      if (pollingTimer) {
        clearInterval(pollingTimer);
        pollingTimer = null;
      }
    };
  }

  /* ─── Simulator Submit ─── */
  simForm.addEventListener("submit", async e => {
    e.preventDefault();
    const payload = {
      gate_congestion:       { A: $("sim-gateA").value, B: $("sim-gateB").value, C: $("sim-gateC").value, D: $("sim-gateD").value },
      elevator_status:       { A: $("sim-elevA").value, B: $("sim-elevB").value, C: $("sim-elevC").value, D: $("sim-elevD").value },
      transit_status:        $("sim-transit").value,
      sensory_room_occupancy:$("sim-sensory").value,
      active_alert:          $("sim-alert").value.trim() || null,
    };
    const key = $("sim-key").value;
    try {
      const res = await fetch("/api/stadium/status", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Ops-Key": key
        },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        renderTelemetry(await res.json());
        toast(t("toastApplied"), "success");
      } else {
        const errData = await res.json().catch(() => ({}));
        toast(errData.detail || t("toastFailed"), "error");
      }
    } catch (err) {
      console.error("Apply Overrides failed", err);
      toast(t("toastFailed"), "error");
    }
  });

  /* ─── Health Check ─── */
  fetch("/health")
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      const dot = $("llm-dot"), txt = $("llm-status-text");
      if (!data || data.status !== "ok") return;
      if (data.llm_online) {
        txt.textContent = "AI Online (Claude)";
        dot.className = "pulse-dot online";
      } else {
        txt.textContent = "Offline Guide";
        dot.className = "pulse-dot offline";
      }
      if (data.max_message_chars && msgInput) {
        msgInput.maxLength = data.max_message_chars;
      }
    })
    .catch(err => { console.error("fetch /health failed", err); });

  /* ─── Init ─── */
  fetchStatus();
  connectSSE();

  if (roleSel) {
    roleSel.addEventListener("change", connectSSE);
  }
  if (locInput) {
    locInput.addEventListener("change", connectSSE);
  }
  $$('input[name="need"]').forEach(checkbox => {
    checkbox.addEventListener("change", connectSSE);
  });

})();
