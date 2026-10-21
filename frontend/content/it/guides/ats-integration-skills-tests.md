---
title: "Come collegare i test di competenze al tuo ATS"
seoTitle: "Collegare i test di competenze all'ATS: guida pratica"
description: "Invia i test di competenze e ricevi i risultati nel tuo ATS in automatico, lascia le decisioni alle persone e scopri cosa controllare per primo."
updated: "2026-10-21"
---

# Come collegare i test di competenze al tuo ATS

La maggior parte dei team di selezione gestisce i candidati in un applicant tracking system (ATS) e fa i test di competenze in un altro strumento. Senza un collegamento tra i due, qualcuno copia le email dall'ATS, invia gli inviti a mano, aspetta e poi ricopia i punteggi. Con cinque candidati funziona. Con cinquanta, gli inviti partono in ritardo, i risultati restano in una seconda scheda che nessuno apre e i candidati migliori accettano altre offerte mentre aspettano.

Questa guida spiega cosa fa un buon collegamento tra un ATS e uno strumento di test, cosa verificare prima di affidartici e come configurarlo perché l'automazione si occupi del lavoro ripetitivo mentre le persone continuano a prendere ogni decisione di assunzione.

## Perché collegarli

| Senza collegamento | Con il collegamento |
| --- | --- |
| Qualcuno esporta o copia le email dei candidati | Spostare un candidato in una fase invia l'invito |
| Gli inviti partono quando qualcuno ha tempo | Gli inviti partono pochi minuti dopo lo spostamento |
| I risultati restano nello strumento di test | I risultati compaiono sul candidato nell'ATS |
| I responsabili delle assunzioni chiedono "qualcuno l'ha già valutato?" | L'ATS mostra chi è stato valutato e com'è andato |
| Errori di battitura nelle email e candidati dimenticati | L'ATS è l'unico elenco di chi si è candidato |

La rapidità conta più di quanto sembri. Più tempo passa tra la candidatura e la risposta, più candidati si ritirano o accettano un altro lavoro. I tassi di abbandono esatti variano molto in base al ruolo e al mercato, quindi prendi con cautela i dati pubblicati, ma la direzione è costante: un processo lento perde persone, e i candidati più forti di solito hanno più alternative.

## Com'è un buon flusso

Una buona integrazione segue le fasi che usi già. Non inventa un nuovo processo.

1. **Un candidato si candida** e arriva nel tuo ATS come sempre.
2. **Una persona lo sposta in una fase di test,** ad esempio "Test delle competenze". Lo spostamento è l'evento che fa partire tutto, quindi è sempre una persona a decidere chi viene valutato.
3. **Lo strumento di test invia l'invito** in automatico, per il test collegato a quella posizione.
4. **Il candidato fa il test** quando gli è comodo, entro la scadenza che fissi.
5. **I risultati vengono registrati sul candidato nell'ATS:** il punteggio, se ha superato il test, eventuali segnalazioni di integrità e un link a tutte le risposte.
6. **Una persona esamina il risultato** e fa avanzare il candidato, oppure no.

Due cose restano manuali di proposito: scegliere chi viene valutato e decidere cosa succede dopo. Il collegamento elimina solo il copia e incolla nel mezzo.

### Perché non partire a ogni nuova candidatura?

Alcuni strumenti invitano chiunque si candidi. Può andare bene per ruoli ad alto volume in cui tutti fanno lo stesso test. Ma una fase in cui sposti i candidati è più facile da controllare: puoi saltare chi chiaramente non soddisfa un requisito indispensabile (niente permesso di lavoro, sede sbagliata) e non valuti mai, né paghi, qualcuno che avresti comunque scartato.

## Cosa controllare prima di scegliere un'integrazione

Non tutti i "si integra con il tuo ATS" significano la stessa cosa. Fai queste domande prima di collegare qualsiasi cosa.

| Domanda | Perché conta | Una buona risposta |
| --- | --- | --- |
| Come avviene il collegamento? | Password condivise e account gestiti dal fornitore sono difficili da verificare o revocare | Una chiave API o un token che la tua azienda crea e può eliminare in qualsiasi momento |
| Cosa può fare la chiave? | Una chiave con accesso completo è un rischio se trapela | I permessi minimi di cui l'integrazione ha bisogno, elencati nella documentazione |
| Cosa fa partire un invito? | Devi sapere esattamente quando i candidati ricevono un'email | Una fase precisa che scegli tu, per ogni posizione |
| Dove arrivano i risultati? | Risultati che nessuno vede non servono | Sul profilo del candidato, come nota o commento che il tuo team legge già |
| Cosa succede se un invito non va a buon fine? | Crediti esauriti, un errore di battitura, un account in pausa: candidati bloccati senza che nessuno se ne accorga | Qualcuno viene avvisato, e il candidato può essere invitato di nuovo |
| Un evento può essere elaborato due volte? | Gli ATS rinviano gli eventi; un candidato non dovrebbe ricevere due inviti | Ogni candidato viene invitato una sola volta per test, indipendentemente da quante volte arriva l'evento |
| Come vengono verificati gli eventi in arrivo? | A un indirizzo non verificato si possono inviare eventi falsi | Richieste firmate che lo strumento verifica |
| Per quanto tempo vengono conservati i dati dei candidati? | Le leggi sulla privacy come il GDPR richiedono un periodo di conservazione chiaro | Un limite dichiarato, e la cancellazione quando elimini la posizione, il test o il tuo account |
| Quanto costa? | I piani a utente possono rendere costosa l'automazione | Un costo prevedibile per ogni candidato valutato |

Se il fornitore non sa rispondere con chiarezza alle domande su errori e duplicati, aspettati di scoprirlo a tue spese.

### Protezione dei dati

Collegare due sistemi significa che i dati dei candidati, almeno nomi ed email, passano tra due aziende. Secondo il GDPR e leggi simili, il fornitore dei test è di solito il tuo responsabile del trattamento: ti serve quindi un accordo sul trattamento dei dati (DPA) e devi informare i candidati, nell'informativa privacy o nell'invito, che un test di competenze fa parte del processo. Condividi solo i dati di cui il test ha bisogno. Per saperne di più sugli aspetti legali dei test e dell'IA nella selezione, leggi [Usare l'IA nella selezione del personale è legale nell'UE?](/guides/is-ai-hiring-legal-in-the-eu)

## Checklist per la configurazione

Prima di attivarlo per una posizione reale:

1. **Crea nel tuo ATS una fase solo per il test,** ad esempio "Test delle competenze". Non riusare una fase che significa altro, o i candidati verranno invitati per errore.
2. **Crea la chiave da un account amministratore** che vede tutte le posizioni che vuoi collegare, solo con i permessi indicati nella documentazione.
3. **Collega ogni posizione al suo test** e scegli la fase che fa partire l'invito.
4. **Configura il webhook** se il tuo ATS richiede di farlo a mano, e incolla il suo secret dove lo strumento lo chiede.
5. **Fai una prova su di te.** Aggiungi un candidato con la tua email, spostalo nella fase, fai il test e controlla che la nota compaia nell'ATS.
6. **Decidi chi tiene d'occhio gli errori:** chi viene avvisato quando un invito non può partire, e chi risolve il problema.
7. **Concorda con il team come leggere i risultati.** Una soglia di superamento è un riferimento, non uno scarto automatico. Decidilo prima che arrivino i risultati, non dopo.

## Errori comuni

- **Automatizzare la decisione, non le pratiche.** Scartare in automatico tutti quelli sotto un punteggio elimina il controllo umano che coglie una domanda sbagliata o un candidato che ha avuto problemi di connessione. Lascia che il punteggio ordini; lascia che sia una persona a decidere.
- **Partire dalla fase sbagliata.** Una fase che i recruiter usano per altri motivi invia test a persone che non dovrebbero riceverli.
- **Un solo test per tutte le posizioni.** Il collegamento rende facile inviare lo stesso test ovunque. Un test è più utile quando è costruito per la posizione in questione. Vedi [Test di competenze o screening dei CV](/guides/skills-tests-vs-cv-screening).
- **Nessuno controlla gli errori.** Se un invito fallisce in silenzio, il candidato aspetta un'email che non arriva mai, e tu pensi che l'abbia ignorata.
- **Una chiave legata a qualcuno che se ne va.** Alcune chiavi degli ATS agiscono a nome della persona che le ha create. Quando il suo account viene chiuso, il collegamento si interrompe. Usa un account che resterà, e ricollega quando le persone cambiano ruolo.
- **Dimenticare i candidati fuori dall'ATS.** Le segnalazioni interne e le candidature dirette che non entrano mai nell'ATS hanno comunque bisogno di un invito. Tieni anche un modo manuale per invitarli.

## Come funziona con prepza

prepza si collega a **Workable, Greenhouse, Teamtailor, Recruitee e Breezy HR** e segue il flusso descritto sopra.

- **La tua chiave, il tuo controllo.** Un proprietario o un amministratore collega l'ATS nella scheda Integrazioni dell'azienda con una chiave che la tua azienda crea nell'ATS. prepza la verifica prima di salvarla, la conserva cifrata e non la mostra mai più. Scollegando l'ATS, la chiave e le posizioni collegate vengono eliminate subito.
- **Collega una posizione a un colloquio.** Scegli una posizione dell'ATS e la fase che fa partire l'invito, e collegala a un colloquio prepza esistente o creane uno nuovo dal testo della posizione nell'ATS. Rivedi gli argomenti prima che venga scritta qualsiasi domanda.
- **Sposti il candidato, l'invito parte.** Ogni candidato viene invitato una sola volta per colloquio, anche se l'ATS invia lo stesso evento due volte.
- **Risultati di nuovo nell'ATS.** Quando un candidato termina, prepza gli aggiunge nell'ATS una nota o un commento con il suo punteggio, se ha superato il test, eventuali segnalazioni di integrità (uscita dalla pagina, tentativi di copia, risposte scelte troppo in fretta per aver letto la domanda) e un link alla sua scheda di valutazione con tutte le risposte.
- **Gli errori non passano inosservati.** Se un candidato non può essere invitato, ad esempio perché l'azienda ha esaurito i crediti, ha raggiunto un limite di email, o perché prepza ha messo temporaneamente in pausa gli inviti, tutti i membri dell'azienda ricevono una notifica che indica l'ATS. I candidati non invitati per mancanza di crediti vengono invitati automaticamente dopo una ricarica, e i candidati in attesa di qualsiasi posizione possono essere invitati di nuovo con un clic.
- **Slack, se lo usi.** prepza può pubblicare notifiche, come un candidato che ha finito o un candidato dell'ATS che non è stato possibile invitare, in un canale Slack a tua scelta.
- **La tua piattaforma.** Se il tuo ATS non è nell'elenco, l'[API](/api-docs) di prepza ti permette di invitare candidati con una chiave API e di ricevere un webhook firmato quando un candidato inizia, termina o viene rimosso, quando il suo invito non gli arriva o scade, e quando un colloquio è pronto.
- **Dati conservati per un periodo stabilito.** I candidati arrivati da un ATS vengono eliminati dopo 365 giorni, o prima insieme al loro colloquio o alla loro azienda.

Alcuni ATS richiedono un passaggio dal loro lato. Greenhouse, Teamtailor e Recruitee ti chiedono di aggiungere un webhook a mano; la finestra Istruzioni di prepza mostra l'indirizzo e dove incollare il suo secret. I webhook di Workable e Breezy HR li configura prepza da solo.

Il prezzo è per candidato, senza abbonamento: paghi solo per i candidati che rispondono ad almeno una domanda, $5 ciascuno con la ricarica da $50, $4 da una ricarica di $200, $3 da una ricarica di $600 e $2 da una ricarica di $1.000. I prezzi sono in dollari USA, in euro in Europa (stessi importi) e in sterline nel Regno Unito (da £4 a £1,50); IVA o sales tax vengono gestite al pagamento. Collegare un ATS e creare colloqui è gratuito, e i primi 3 candidati della tua prima azienda sono gratis. Vedi i [prezzi](/pricing).

## Letture correlate

- [Come fare lo screening di 100 candidati in un giorno](/guides/screen-100-applicants-in-a-day)
- [Test di competenze o screening dei CV](/guides/skills-tests-vs-cv-screening)
- [Test pre-assunzione: una guida pratica](/pre-employment-testing)
