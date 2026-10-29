# The FAQ in it; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "Cos'è prepza?",
        "answer": "Un colloquio a tempo creato dalla tua descrizione del ruolo, per qualsiasi ruolo. Usalo per selezionare i candidati prima di incontrarli, o come fase vera e propria dell'assunzione: in entrambi i casi vedi chi conosce davvero il lavoro.",
    },
    {
        "key": "roles",
        "question": "Per quali ruoli posso assumere?",
        "answer": "Qualsiasi ruolo in cui contano le conoscenze: assistenza, vendite, finanza, sanità, mestieri tecnici, ingegneria, marketing e altro. Se puoi descrivere il lavoro, prepza può creare un colloquio per esso.",
    },
    {
        "key": "hiring",
        "question": "Come funziona?",
        "answer": "Incolla una descrizione del ruolo nella home page, indica il nome della tua azienda e controlla gli argomenti che propone prepza. Poi invita i candidati: scrivi le loro email, incolla un elenco o carica un file. I candidati che non hanno iniziato dopo qualche giorno ricevono un promemoria. Ogni candidato riceve domande tutte sue, ciascuna con un timer, e vedi il suo punteggio e ogni risposta appena finisce.",
    },
    {
        "key": "link",
        "question": "Posso mettere un colloquio in un annuncio di lavoro?",
        "answer": "Sì. Attiva il link condivisibile del colloquio nella sua scheda Impostazioni e incollalo nel tuo annuncio. Chiunque lo apra accede e svolge il colloquio, e ogni persona ti costa quanto un candidato invitato. Il link si disattiva quando segni il colloquio come «Assunto».",
    },
    {
        "key": "preview",
        "question": "Posso provare un colloquio prima di invitare qualcuno?",
        "answer": "Sì. Apri il tuo colloquio come candidato dalla sua pagina, gratis: le anteprime non compaiono tra i tuoi candidati né nelle statistiche delle domande. Puoi anche fare una qualsiasi delle simulazioni di colloquio gratuite.",
    },
    {
        "key": "cheating",
        "question": "I candidati possono usare l'IA o cercare le risposte?",
        "answer": "Ogni candidato riceve domande casuali tutte sue, in un ordine tutto suo, con [un timer su ogni domanda](/guides/skills-test-timing-and-extra-time) gestito dal nostro server, quindi c'è poco tempo per cercare le risposte o chiedere a un'IA. Le schede di valutazione mostrano anche quando un candidato ha lasciato la pagina, copiato del testo o risposto troppo in fretta per aver letto la domanda. Prima di iniziare, ogni candidato conferma anche che risponderà in autonomia, senza strumenti di IA né l'aiuto di altre persone, e la sua scheda di valutazione lo mostra.",
    },
    {
        "key": "cost",
        "question": "Quanto costa?",
        "answer": "Generare colloqui è gratis. Ogni candidato che risponde ad almeno una domanda costa {candidate} crediti ({candidate_price}), e meno con i crediti di ricariche più grandi, fino a {cheapest_price}. La tua prima azienda riceve {company} crediti gratuiti, sufficienti per i suoi primi {company_candidates} candidati. La [pagina dei prezzi](/pricing) elenca ogni prezzo.",
    },
    {
        "key": "charged",
        "question": "Quando viene addebitato un candidato?",
        "answer": "Purché abbia risposto ad almeno una domanda: quando il suo colloquio termina (lo conclude lui, o il tempo scade mentre è assente), oppure quando lo revochi. Una domanda il cui tempo è scaduto senza una risposta scelta non conta. I suoi crediti vengono messi da parte quando lo inviti e tornano se lo revochi prima che risponda a qualcosa, se non inizia mai o se il suo colloquio termina senza alcuna risposta.",
    },
    {
        "key": "compare_hiring",
        "question": "Come si confronta il prezzo con altri strumenti di valutazione?",
        "answer": "Molti strumenti di valutazione sono venduti in abbonamento mensile o annuale, che paghi anche se non valuti nessuno. Con prepza paghi solo per candidato: {candidate} crediti ({candidate_price}), senza contratto, senza costi per utente e senza pagare per generare un colloquio. Un’azienda che invita {example_candidates} candidati al mese paga circa {example_year_price} all’anno. Se valuti molti candidati ogni mese, un abbonamento può costare meno, quindi confronta con i tuoi numeri.",
    },
    {
        "key": "expire",
        "question": "I crediti scadono?",
        "answer": "No. I crediti non scadono mai, e non ci sono abbonamenti a pagamento. Se attivi la ricarica automatica facoltativa, Paddle salva la tua carta come abbonamento da {zero_price}; paghi solo le ricariche che effettua.",
    },
    {
        "key": "currency",
        "question": "In che valuta pago?",
        "answer": "I prezzi sono nella valuta locale in Canada, Australia, Israele, Polonia, Svizzera, Giappone, Corea del Sud, Taiwan, Hong Kong, Thailandia, Singapore e India; in euro nel resto dell'UE e in Islanda, nel Liechtenstein e in Norvegia; in sterline nel Regno Unito; e in dollari statunitensi altrove. Il tuo account e ogni azienda mantengono la valuta del paese in cui sono stati creati, ovunque tu viaggi: cambia la tua nelle Impostazioni e quella di un'azienda accanto al suo pulsante Ricarica (proprietari e amministratori). Le ricariche di un'azienda, anche quelle automatiche, vengono sempre addebitate nella valuta dell'azienda.",
    },
    {
        "key": "refunds",
        "question": "Posso avere un rimborso?",
        "answer": "Sì, per i crediti acquistati negli ultimi 14 giorni e non ancora spesi: tramite Paddle o scrivendoci. I crediti gratuiti, come il regalo di benvenuto, non sono rimborsabili. I [termini](/terms) riportano i dettagli.",
    },
    {
        "key": "scorecards",
        "question": "Cosa mostrano le schede di valutazione?",
        "answer": "Ogni risposta, se era giusta e quanto tempo ha richiesto. Il punteggio è la percentuale di punti ottenuti: ogni domanda vale un punto, e una domanda in cui selezionare tutte le risposte corrette ne dà una parte per ogni opzione corretta selezionata, e niente se ne è selezionata una sbagliata. I punteggi compaiono in verde o in rosso rispetto alla soglia di superamento che hai impostato per il colloquio. Le schede segnalano anche risposte troppo veloci per aver letto la domanda, le uscite dalla pagina e i tentativi di copia.",
    },
    {
        "key": "reports",
        "question": "Posso condividere i risultati con un responsabile delle assunzioni?",
        "answer": "Sì. Scarica un report PDF per un candidato o per tutti i candidati di un colloquio, invialo via email direttamente da prepza, oppure manda un breve riepilogo su WhatsApp, Telegram, Viber o LINE.",
    },
    {
        "key": "action_log",
        "question": "Posso vedere chi ha fatto cosa nella mia azienda?",
        "answer": "Sì, se sei il proprietario dell'azienda. La sua scheda Registro attività elenca tutto ciò che hanno fatto i membri, dal più recente: invitare o rimuovere candidati, vedere i risultati, modificare colloqui, team, fatturazione e integrazioni, con chi l'ha fatto, quando e se l'ha fatto per suo conto l'assistente, un'app di IA o l'API. Puoi filtrarlo per membro, tipo di azione e date. Le attività vengono conservate per 12 mesi.",
    },
    {
        "key": "integrations",
        "question": "prepza funziona con il mio ATS o con altri strumenti?",
        "answer": "Sì, senza costi aggiuntivi. Collega Workable, Greenhouse, Teamtailor, Recruitee o Breezy HR nella scheda Integrazioni della tua azienda: i candidati che sposti in una fase ricevono il colloquio, e i loro risultati tornano nell'ATS ([come collegare i test di competenze al tuo ATS](/guides/ats-integration-skills-tests)). Slack può pubblicare le notifiche della tua azienda in un canale, e l'API permette alla tua piattaforma di creare colloqui, invitare e gestire candidati e ricevere i loro risultati, con ogni chiave API limitata a ciò che spunti per lei; consulta la [Documentazione API](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Posso usare prepza da Claude, ChatGPT o da un mio agente IA?",
        "answer": "Sì. Aggiungi prepza a Claude o ChatGPT come connettore (i passaggi sono nella scheda Integrazioni della tua azienda) e consenti l'accesso su prepza. L'app lavora quindi con le tue aziende, i colloqui e i risultati dei candidati a tuo nome, con i tuoi permessi; la maggior parte delle app ti chiede conferma prima di modificare qualcosa. L'account o un'azienda si eliminano solo in prepza. Ciò che l'app legge arriva al suo fornitore, secondo i termini di quell'app. Puoi scollegarla in qualsiasi momento nella stessa scheda. Si collegano anche altre app di IA e gli agenti che crei tu: la [scheda MCP](/api-docs?tab=mcp) della documentazione per sviluppatori ha i passaggi e agenti di esempio, e un agente su un server può accedere con una chiave API che ha il permesso per gli agenti IA. La [guida ad agenti IA, MCP e API](/guides/ai-agents-mcp-and-api) spiega a cosa serve ciascuno.",
    },
    {
        "key": "candidates",
        "question": "Cosa vedono i candidati?",
        "answer": "Il nome e il logo della tua azienda, con i colori e i caratteri della tua azienda (impostati nella sua scheda Brand), cosa aspettarsi prima di iniziare, poi una domanda a tempo alla volta. Non vedono mai il punteggio né se una risposta era giusta.",
    },
    {
        "key": "verified",
        "question": "Cosa significa la spunta di verifica?",
        "answer": "Che un proprietario o un amministratore dell'azienda ha effettuato l'accesso con un'email di lavoro sul sito dell'azienda, ad esempio nome@acme.com, e che poi il nostro team ha esaminato l'azienda. Aggiungi il sito con Verifica nell'intestazione della tua azienda; i servizi email gratuiti non contano. Finché la revisione è in attesa, il tuo team vede un orologio accanto al nome, e rinominare l'azienda la rimanda in revisione. La spunta compare accanto al nome della tua azienda, anche negli inviti.",
    },
    {
        "key": "languages",
        "question": "Quali lingue sono supportate?",
        "answer": "{count} lingue, per il sito, i colloqui e le email. Scegli la lingua in cui è scritto un colloquio, qualunque sia la lingua della descrizione del ruolo.",
    },
    {
        "key": "privacy",
        "question": "Cosa succede alle descrizioni dei ruoli e alle risposte?",
        "answer": "Le descrizioni dei ruoli servono a creare i colloqui della tua azienda, e le risposte dei candidati a valutarli per la tua azienda. Le domande generate da prepza possono anche essere riutilizzate nei colloqui e nelle simulazioni di altre aziende, senza nulla che identifichi te, la tua azienda o chiunque altro; puoi escludere da questo riutilizzo le domande di un colloquio nelle sue impostazioni. prepza ricava inoltre dalle risposte date alle domande tendenze generali e anonimizzate sulla loro qualità, per migliorare il modo in cui le domande vengono generate. L'[informativa sulla privacy](/privacy) spiega cosa conserviamo, per quanto tempo e i diritti di ciascuno.",
    },
    {
        "key": "eu_ai_law",
        "question": "È legale usare l'IA per la preselezione dei candidati nell'UE?",
        "answer": "Sì, con delle regole. Secondo il regolamento europeo sull'IA (AI Act), gli strumenti che valutano i candidati sono molto probabilmente ad alto rischio, con obblighi dal 2 dicembre 2027, e il GDPR si applica già: una persona prende la decisione di assunzione, i candidati vengono informati che si usa l'IA e si conserva una documentazione. prepza funziona così: l'IA scrive le domande, le persone della tua azienda esaminano i risultati e decidono, e i candidati vengono informati prima di iniziare. Questa non è una consulenza legale; [Usare l'IA nella selezione del personale è legale nell'UE?](/guides/is-ai-hiring-legal-in-the-eu) spiega le regole e le date.",
    },
    {
        "key": "emails",
        "question": "Quali email invia prepza e come posso interromperle?",
        "answer": 'Le email di servizio, come inviti, report, problemi di pagamento e modifiche ai nostri termini, vengono sempre inviate. Le altre, come il riepilogo attività giornaliero, i promemoria e le novità sul prodotto, le scegli nelle Impostazioni, alla voce Email, oppure le interrompi con il link "Annulla l\'iscrizione" in ogni email. I candidati possono interrompere le email della tua azienda, o i promemoria di un colloquio, con i link nei loro inviti e promemoria.',
    },
    {
        "key": "delete",
        "question": "Posso eliminare il mio account?",
        "answer": "Sì, nelle Impostazioni. Il tuo account e i tuoi dati vengono eliminati, e prima puoi scaricarne una copia. Le novità di prepza compaiono nelle tue notifiche, la campanella in alto; quelle più importanti arrivano anche via email come novità sul prodotto, solo finché quell'impostazione è attiva.",
    },
    {
        "key": "report",
        "question": "Come segnalo un problema?",
        "answer": "Scrivici dalla [pagina dei contatti](/contact) e incolla l'ID di ciò di cui si tratta: «copia id» è sotto il nome di un'azienda, di un colloquio o di un candidato, e quello del tuo account è nel menu dell'account e nelle Impostazioni. Con l'ID lo troviamo subito.",
    },
]
