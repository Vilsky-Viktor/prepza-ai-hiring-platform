---
title: "Agenti IA, MCP e API: cosa sono e come usarli nella selezione del personale"
seoTitle: "Agenti IA, MCP e API nella selezione del personale"
description: "Cosa sono agenti IA, MCP e API, come usarli in sicurezza nella selezione e gestire prepza dalla sua assistente IA, Claude, ChatGPT o la tua piattaforma."
updated: "2026-10-22"
---

# Agenti IA, MCP e API: cosa sono e come usarli nella selezione del personale

La maggior parte delle persone ha conosciuto l'IA come una finestra di chat: fai una domanda e lei risponde. Un agente IA fa un passo in più. Può cercare informazioni nei tuoi strumenti e, quando glielo chiedi, agire al loro interno: creare un colloquio, invitare un elenco di candidati, dirti chi ha ottenuto il punteggio più alto la settimana scorsa. Il Model Context Protocol (MCP) è lo standard che permette alla chat IA che usi già, come Claude o ChatGPT, di collegarsi a strumenti come questi. E un'API è il modo più vecchio e più preciso con cui un software parla con un altro, senza IA in mezzo.

Questa guida spiega tutti e tre in parole semplici, a cosa servono nella selezione del personale, a cosa fare attenzione e come usarli con prepza.

## Cos'è un agente IA

Un chatbot scrive solo testo. Un agente è un modello linguistico con degli **strumenti**: piccole azioni ben definite che può richiamare, come «elenca i candidati di questo colloquio» o «invita questa email». Quando gli chiedi qualcosa, l'agente decide quali strumenti usare, legge cosa restituiscono e risponde in base a quello, non a memoria.

| Un chatbot | Un agente IA |
| --- | --- |
| Risponde con ciò che ha imparato durante l'addestramento | Risponde con i tuoi dati aggiornati, letti tramite gli strumenti |
| Può solo descrivere come si fa qualcosa | Può farlo, quando glielo chiedi e lo consenti |
| Tira a indovinare quando non sa | Verifica, oppure dice che non può |
| Vive in una sola finestra | Lavora dentro gli strumenti a cui lo colleghi |

Sono gli strumenti a rendere utile un agente, e anche a renderlo sicuro o meno. Un buon agente può usare solo gli strumenti che gli vengono dati, solo con i tuoi permessi, e fa solo quello che hai chiesto.

## Cos'è MCP

Il Model Context Protocol è uno standard aperto, presentato da Anthropic alla fine del 2024 e oggi supportato da Claude, ChatGPT e da molte altre app di IA e strumenti per sviluppatori. Viene spesso paragonato a una porta USB-C per l'IA: invece di far costruire a ogni app di IA il proprio collegamento con ogni strumento, uno strumento offre un unico **server MCP**, e qualsiasi app di IA che parla MCP può usarlo.

Un server MCP dice tre cose all'app di IA:

1. **Quali strumenti esistono**, con un nome, una descrizione e i dati che servono a ciascuno.
2. **Quali strumenti si limitano a leggere** e quali modificano qualcosa, così l'app di IA può chiederti conferma prima di una modifica.
3. **Chi sei**, tramite un accesso che approvi una sola volta, così ogni chiamata viene eseguita a tuo nome, con i tuoi permessi.

Per te significa poter lavorare con uno strumento dalla chat che usi già, senza copiare dati da una finestra all'altra.

## Cos'è un'API e in cosa è diversa

Un'API (interfaccia di programmazione delle applicazioni) è un insieme di richieste fisse che un programma può inviare a un altro: «elenca i candidati di questo colloquio», «invita questa email». Gli sviluppatori scrivono il codice che le invia. Non c'è IA di mezzo: la stessa richiesta fa sempre la stessa cosa, ed è proprio quello che vuoi da un'automazione che funziona da sola.

| | Mira, l'assistente IA (nell'app) | MCP (in Claude o ChatGPT) | API |
| --- | --- | --- | --- |
| Chi lo usa | Tu, in prepza | Tu, nella tua chat IA | Il codice della tua piattaforma |
| Come si chiede | Con parole tue | Con parole tue | Richieste fisse scritte da uno sviluppatore |
| Chi approva le modifiche | Tu, su una scheda | Tu, nella tua app di IA | Il tuo codice, così come è scritto |
| Ideale per | Domande e attività veloci | Usare prepza insieme agli altri tuoi strumenti e file | Automazioni che girano senza che nessuno le controlli |
| Accede come | Te | Te | Una chiave aziendale |

Usa Mira o MCP quando c'è una persona a seguire il processo. Usa l'API quando il tuo sistema deve invitare i candidati e raccogliere i risultati da solo, per esempio da un sito carriere o da uno strumento HR interno.

## A cosa serve nella selezione del personale

La selezione è fatta di tanti piccoli passaggi ripetitivi, sparsi tra vari strumenti. Un agente è bravo proprio in questo:

- **Domande sulla tua pipeline.** «Quali candidati per Senior Backend hanno superato il test questa settimana?», «Chi non ha ancora iniziato il colloquio?», «Qual è il nostro punteggio medio per il ruolo di data analyst?»
- **Configurare.** «Crea un colloquio da questa descrizione del ruolo», «Imposta la soglia di superamento al 70%», «Dai a questo candidato il 50% di tempo in più.»
- **Operazioni in blocco.** «Invita queste 12 persone al colloquio frontend», incollato direttamente da un'email o da un foglio di calcolo.
- **Combinare le fonti.** In Claude o ChatGPT puoi usare prepza insieme agli altri strumenti e file collegati: confrontare una descrizione del ruolo nei tuoi documenti con gli argomenti del colloquio, o preparare un messaggio per i candidati in shortlist.

Quello che non deve fare è prendere la decisione di assunzione. Un punteggio supporta il giudizio di una persona, non lo sostituisce. Chiedi all'agente di ordinare, riassumere e preparare, e lascia la decisione a una persona. Leggi [Usare l'IA nella selezione del personale è legale nell'UE?](/guides/is-ai-hiring-legal-in-the-eu) per capire perché conta anche dal punto di vista legale.

## A cosa fare attenzione

Collegare un'IA ai tuoi dati di selezione richiede la stessa cura che serve per dare accesso a un collega.

| Rischio | Cosa aiuta |
| --- | --- |
| L'agente fa qualcosa che non intendevi | Le modifiche richiedono prima la tua approvazione, e fa solo quello che hai chiesto |
| Vede più di quanto dovrebbe | Agisce a tuo nome: vede quello che vedi tu, niente di più |
| Istruzioni nascoste nei dati | Nomi, risposte e documenti dei candidati sono dati, mai istruzioni da seguire |
| Segreti che finiscono in una chat | Chiavi API e password non passano mai dalla chat |
| Errori irreversibili | L'eliminazione di un account o di un'azienda resta nell'app, con la sua conferma dedicata |
| Dati che escono dai tuoi strumenti | I dati arrivano all'app di IA che colleghi, alle condizioni di quell'app: collega solo app consentite dalla tua azienda |
| Utilizzo fuori controllo | Limiti al numero di azioni eseguite ogni ora |

Prima di collegare qualsiasi app di IA a dati di lavoro, verifica la policy della tua azienda sugli strumenti di IA e indica ai candidati, nell'informativa sulla privacy, quali servizi trattano i loro dati.

## Tre modi di lavorare con prepza oltre le sue pagine

### 1. Mira, l'assistente IA integrata

Seleziona **chiedi a Mira** nell'intestazione di qualsiasi pagina. Mira, l'assistente IA di prepza, conosce le tue aziende, i colloqui, i candidati, i crediti e le integrazioni, e sa come funziona prepza. Risponde nella tua lingua, e puoi scrivere o parlare.

- **Risponde con i tuoi dati**, con la stessa visibilità che hai tu: un amministratore vede quello che vede un amministratore, un visualizzatore quello che vede un visualizzatore.
- **Sa in quale pagina ti trovi.** Chiedi «Cosa posso fare in questa pagina?» per la guida di quella pagina, oppure «Chi è il migliore qui?» sui candidati di un colloquio, e risponde su quel colloquio senza chiederti quale.
- **Prepara le modifiche, tu le confermi.** Se gli chiedi di invitare candidati, mostra una scheda con esattamente quello che succederà, per esempio «Invita 12 candidati a Backend developer». Non parte nulla finché non selezioni Conferma.
- **Mostra le sue fonti.** Sotto una risposta trovi i candidati o i colloqui che ha usato e un link alla pagina da cui provengono.
- **Resta in tema.** Risponde su prepza e sulla selezione del personale con prepza, e declina il resto.

### 2. prepza in Claude o ChatGPT, tramite MCP

Se il tuo team lavora già in Claude o ChatGPT, puoi portare lì prepza. Il server MCP di prepza offre gli stessi strumenti di Mira, l'assistente integrata.

**Per collegarlo:**

1. In prepza, apri la scheda **Integrazioni** di un'azienda e seleziona **App IA**. Copia l'indirizzo del server: `https://prepza.ai/mcp`.
2. **In Claude:** apri Impostazioni, poi Connettori, e aggiungi un connettore personalizzato con quell'indirizzo. **In Claude Code:** esegui `claude mcp add --transport http prepza https://prepza.ai/mcp`. **In ChatGPT:** aggiungilo come connettore personalizzato nelle impostazioni di app e connettori.
3. La tua app di IA apre la pagina di accesso di prepza. Accedi, controlla quale app sta facendo la richiesta e seleziona **Consenti**. Perché possa solo leggere, disattiva prima **Consenti modifiche**.

Da quel momento, chiedi nella chat come faresti con un collega: «In prepza, chi sono i tre migliori candidati per Product designer?» La maggior parte delle app di IA ti chiede conferma prima di una modifica e ti avvisa prima di qualsiasi operazione che non si può annullare: prepza indica loro quali azioni modificano o eliminano qualcosa.

**Cosa resta uguale rispetto all'app:**

- **I tuoi permessi.** Agisce a tuo nome, in ogni azienda di cui fai parte, con il tuo ruolo in ciascuna.
- **Crediti e limiti.** Invitare un candidato costa come nell'app, e valgono gli stessi limiti di email.
- **La tracciabilità.** Tutto ciò che un'app di IA fa per te compare nel registro attività dell'azienda come fatto tramite un'app di IA, dall'approvare argomenti e vedere risultati al concedere tempo extra o revocare un candidato. Il proprietario dell'azienda lo legge nella scheda **Registro attività** dell'azienda.
- **Decide l'azienda.** Proprietari e amministratori possono impedire alle app di IA di usare i dati di un'azienda con **Consenti le app di IA in questa azienda** nella sua pagina delle app di IA.
- **Cosa non può fare.** Non può vedere la tua password né le tue chiavi API, e non può eliminare il tuo account o un'azienda. Queste operazioni restano nell'app.

**Per scollegarlo,** rimuovi il connettore nella tua app di IA, oppure seleziona **Scollega** accanto a esso in **App IA**, nella scheda Integrazioni. Smette di funzionare subito.

**Altre app e i tuoi agenti.** La [scheda MCP](/api-docs?tab=mcp) della documentazione per sviluppatori contiene i passaggi per Gemini CLI, Cursor, VS Code e Le Chat, e agenti di esempio completi in Python e TypeScript. Un agente che gira su un server, senza nessuno che approvi un accesso, usa una chiave API dell'azienda con il permesso **Uso con agenti IA (MCP)**: funziona solo in quell'azienda e solo con gli strumenti consentiti dagli altri permessi della chiave.

### 3. La tua piattaforma, tramite l'API

Per automazioni senza IA, prepza ha un'API, descritta nella sua [documentazione per sviluppatori](/api-docs).

1. Un proprietario o un amministratore apre la scheda **Integrazioni** di un'azienda, poi **API**, e seleziona **Nuova chiave**. Dalle il nome della piattaforma che la userà, scegli quando scade e spunta solo ciò che le serve: la chiave di una dashboard legge soltanto, quella di un sito carriere invita anche. Potrai togliere permessi in seguito, mai aggiungerne. La chiave viene mostrata una sola volta: conservala in un posto sicuro.
2. La tua piattaforma invia richieste con quella chiave: elencare i colloqui dell'azienda, elencare o leggere i candidati con il loro punteggio, se hanno superato il test e le segnalazioni di integrità, e invitare un candidato.
3. Aggiungi un **webhook**: un indirizzo sulla tua piattaforma che prepza chiama, con una firma, quando un candidato inizia, termina o viene rimosso, quando il suo invito non gli arriva o scade, e quando un colloquio è pronto, così non devi continuare a chiedere. La pagina API può inviargli un evento di test e ne mostra il registro delle consegne.

Ogni candidato arriva con un link ai suoi risultati completi in prepza e, finché non termina, con il suo link di invito, così la tua piattaforma può inviarlo con un proprio messaggio, se preferisci. Quando la tua piattaforma sa già chi è il candidato, invitalo senza accesso: prepza non invia email, e il candidato svolge il colloquio dal link senza accedere a prepza, quindi invia il link solo a lui. Un invito può anche riportare il candidato sul tuo sito con un pulsante nella pagina finale, e impostare un tema chiaro o scuro con i colori della tua azienda. Con l'SDK di prepza, la tua pagina può mostrare il colloquio stesso. Riportare i candidati sul tuo sito e mostrarvi il colloquio richiedono un'azienda verificata, e funzionano solo sul dominio del suo sito web.

Vale la stessa regola di sempre: il punteggio supporta la decisione di una persona, quindi non scartare candidati in automatico sulla base del punteggio.

## Quale usare e quando

Parti da chi fa il lavoro e con quale frequenza.

| La tua situazione | Cosa usare |
| --- | --- |
| Sei in prepza e vuoi una risposta veloce: chi ha superato il test, chi non ha iniziato, quanti crediti restano | Mira, l'assistente integrata |
| Vuoi configurare qualcosa in poche parole: un colloquio da una descrizione del ruolo, una soglia di superamento, più tempo | Mira, l'assistente integrata |
| Lavori già tutto il giorno in Claude o ChatGPT e vuoi avere lì anche prepza | MCP |
| L'attività richiede prepza e qualcos'altro: i tuoi documenti, bozze di email, un altro strumento collegato | MCP |
| Un recruiter in giro vuole controllare la pipeline dall'app di IA sul telefono | MCP |
| Il tuo sito carriere o il tuo sistema HR deve invitare i candidati da solo, senza che nessuno clicchi | L'API |
| I risultati devono arrivare nel tuo database o nella tua dashboard appena i candidati terminano | L'API, con un webhook |
| Il tuo ATS è tra quelli a cui prepza si collega (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Nessuno di questi: collega l'ATS nella scheda Integrazioni. Vedi [Come collegare i test di competenze al tuo ATS](/guides/ats-integration-skills-tests) |

Una regola pratica:

- **Una persona chiede e controlla ogni modifica:** Mira in prepza, oppure MCP se quella persona passa le giornate in Claude o ChatGPT.
- **Un software agisce da solo, sempre allo stesso modo:** l'API.
- **Per iniziare:** prova prima Mira, l'assistente integrata. Non richiede configurazione, e quello che impari ti servirà anche con MCP.

Funzionano anche insieme. Un team può inviare gli inviti dal proprio sistema HR tramite l'API, mentre i recruiter chiedono dei risultati a Mira o alla loro chat IA.

## Come ottenere buoni risultati

- **Chiama le cose per nome.** «Il colloquio Senior Backend» funziona meglio di «quel colloquio».
- **Chiedi un passaggio alla volta** quando conta. Controlla il risultato, poi chiedi il successivo.
- **Leggi la richiesta di conferma prima di consentirla.** Mostra esattamente cosa verrà eseguito.
- **Chiedi da dove viene un numero.** Un buon agente sa indicare i candidati o la pagina su cui si basa.
- **Lascia le decisioni alle persone.** Usa l'agente per trovare, ordinare e preparare; decidi tu.

## Prezzi

Mira, il collegamento MCP e l'API sono gratuiti. Paghi solo i candidati, come sempre: per ogni candidato che risponde ad almeno una domanda, senza abbonamento. Vedi i [prezzi](/pricing).

## Letture correlate

- [Come collegare i test di competenze al tuo ATS](/guides/ats-integration-skills-tests)
- [Colloqui tecnici nell'era dell'IA](/guides/interviewing-in-the-age-of-ai)
- [Usare l'IA nella selezione del personale è legale nell'UE?](/guides/is-ai-hiring-legal-in-the-eu)
