# The FAQ in fr; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "Qu'est-ce que prepza ?",
        "answer": "Un entretien chronométré créé à partir de votre fiche de poste, pour n'importe quel poste. Utilisez-le pour présélectionner les candidats avant de les rencontrer, ou comme une étape à part entière du recrutement : dans les deux cas, vous voyez qui maîtrise vraiment le poste.",
    },
    {
        "key": "roles",
        "question": "Pour quels postes puis-je recruter ?",
        "answer": "Tout poste où les connaissances comptent : support, vente, finance, santé, métiers manuels, ingénierie, marketing et plus encore. Si vous pouvez décrire le poste, prepza peut créer un entretien pour lui.",
    },
    {
        "key": "hiring",
        "question": "Comment ça marche ?",
        "answer": "Collez une fiche de poste sur la page d'accueil, indiquez le nom de votre entreprise et vérifiez les thèmes que propose prepza. Invitez ensuite des candidats : saisissez leurs e-mails, collez une liste ou importez un fichier. Les candidats qui n'ont pas commencé après quelques jours reçoivent un rappel. Chaque candidat reçoit ses propres questions, chacune chronométrée, et vous voyez son score et chaque réponse dès qu'il a terminé.",
    },
    {
        "key": "link",
        "question": "Puis-je mettre un entretien dans une offre d'emploi ?",
        "answer": "Oui. Activez le lien de partage de l'entretien dans son onglet Candidats et collez-le dans votre offre. Toute personne qui l'ouvre se connecte et passe l'entretien, et chacune est facturée comme un candidat invité. Le lien se désactive quand vous marquez l'entretien comme recruté.",
    },
    {
        "key": "preview",
        "question": "Puis-je essayer un entretien avant d'inviter qui que ce soit ?",
        "answer": "Oui. Ouvrez votre entretien en tant que candidat depuis sa page, gratuitement : les aperçus n'apparaissent ni parmi vos candidats ni dans les statistiques des questions. Vous pouvez aussi passer n'importe lequel des entretiens d'entraînement gratuits.",
    },
    {
        "key": "cheating",
        "question": "Les candidats peuvent-ils utiliser une IA ou chercher les réponses ?",
        "answer": "Chaque candidat reçoit ses propres questions aléatoires, dans son propre ordre, avec [un minuteur sur chaque question](/guides/skills-test-timing-and-extra-time) contrôlé par notre serveur, il a donc peu de temps pour chercher les réponses ou demander à une IA. Les résultats montrent aussi quand un candidat a quitté la page, copié du texte ou répondu trop vite pour avoir lu la question.",
    },
    {
        "key": "cost",
        "question": "Combien ça coûte ?",
        "answer": "La génération d'entretiens est gratuite. Chaque candidat qui répond à au moins une question coûte {candidate} crédits ({candidate_dollars} $), et moins avec les crédits de recharges plus importantes, jusqu'à 2 $. Votre première entreprise reçoit {company} crédits gratuits, de quoi couvrir ses {company_candidates} premiers candidats. La [page des tarifs](/pricing) indique tous les prix.",
    },
    {
        "key": "charged",
        "question": "Quand un candidat est-il facturé ?",
        "answer": "À condition qu'il ait répondu à au moins une question : quand son entretien prend fin (il le termine, ou le temps s'écoule pendant son absence), ou quand vous le révoquez. Une question dont le temps s'est écoulé sans réponse choisie ne compte pas. Ses crédits sont mis de côté lorsque vous l'invitez et reviennent si vous le révoquez avant qu'il ait répondu à quoi que ce soit, s'il ne commence jamais ou si son entretien prend fin sans aucune réponse.",
    },
    {
        "key": "compare_hiring",
        "question": "Comment le prix se compare-t-il à celui d'autres outils d'évaluation ?",
        "answer": "Beaucoup d'outils d'évaluation sont vendus sous forme d'abonnement mensuel ou annuel, payé même si vous n'évaluez personne. Avec prepza, vous payez uniquement par candidat : {candidate} crédits ({candidate_dollars} $), sans contrat, sans frais par utilisateur et sans rien à payer pour générer un entretien. Une entreprise qui invite {example_candidates} candidats par mois paie environ {example_year_dollars} $ par an. Si vous évaluez beaucoup de candidats chaque mois, un abonnement peut coûter moins cher : comparez avec vos propres chiffres.",
    },
    {
        "key": "expire",
        "question": "Les crédits expirent-ils ?",
        "answer": "Non. Les crédits n'expirent jamais, et il n'y a aucun abonnement payant. Si vous activez la recharge automatique facultative, Paddle enregistre votre carte sous forme d'abonnement à 0 $ ; vous ne payez que les recharges qu'elle effectue.",
    },
    {
        "key": "refunds",
        "question": "Puis-je être remboursé ?",
        "answer": "Oui, pour les crédits achetés au cours des 14 derniers jours et non dépensés : via Paddle ou en nous écrivant. Les crédits offerts, comme le cadeau de bienvenue, ne sont pas remboursés. Les [conditions](/terms) donnent les détails.",
    },
    {
        "key": "scorecards",
        "question": "Que montrent les fiches d'évaluation des candidats ?",
        "answer": "Chaque réponse, si elle était juste et le temps qu'elle a pris. La note est le pourcentage de points obtenus : chaque question vaut un point, et une question où il faut cocher toutes les bonnes réponses en rapporte une part pour chaque bonne réponse cochée, et rien si une mauvaise est cochée. Les notes s'affichent en vert ou en rouge par rapport au seuil de réussite que vous avez fixé pour l'entretien. Les fiches signalent aussi les réponses trop rapides pour avoir lu la question, les sorties de la page et les tentatives de copie.",
    },
    {
        "key": "reports",
        "question": "Puis-je partager les résultats avec un responsable du recrutement ?",
        "answer": "Oui. Téléchargez un rapport PDF pour un candidat ou pour tous les candidats d'un entretien, envoyez-le par e-mail directement depuis prepza, ou envoyez un court résumé sur WhatsApp, Telegram, Viber ou LINE.",
    },
    {
        "key": "action_log",
        "question": "Puis-je voir qui a fait quoi dans mon entreprise ?",
        "answer": "Oui, si vous êtes propriétaire de l'entreprise. Son onglet Journal des actions liste tout ce que ses membres ont fait, du plus récent au plus ancien : inviter ou retirer des candidats, consulter des résultats, modifier les entretiens, l'équipe, la facturation et les intégrations, avec qui l'a fait, quand, et si l'assistant, une application d'IA ou l'API l'a fait en son nom. Vous pouvez le filtrer par membre, type d'action et dates. Les actions sont conservées 12 mois.",
    },
    {
        "key": "integrations",
        "question": "prepza fonctionne-t-il avec mon ATS ou d'autres outils ?",
        "answer": "Oui, sans frais supplémentaires. Connectez Workable, Greenhouse, Teamtailor, Recruitee ou Breezy HR dans l'onglet Intégrations de votre entreprise : les candidats que vous déplacez vers une étape reçoivent l'entretien, et leurs résultats reviennent dans l'ATS ([comment connecter vos tests de compétences à votre ATS](/guides/ats-integration-skills-tests)). Slack peut publier les notifications de votre entreprise dans un canal, et l'API permet à votre propre plateforme de créer des entretiens, d'inviter et de gérer des candidats et de recevoir leurs résultats, chaque clé API étant limitée à ce que vous cochez pour elle ; consultez la [Documentation de l'API](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Puis-je utiliser prepza depuis Claude, ChatGPT ou mon propre agent IA ?",
        "answer": "Oui. Ajoutez prepza à Claude ou ChatGPT comme connecteur (les étapes sont dans l'onglet Intégrations de votre entreprise) et autorisez-le sur prepza. L'application travaille alors avec vos entreprises, vos entretiens et les résultats des candidats en votre nom, avec vos droits ; la plupart des applications vous demandent avant de modifier quoi que ce soit. La suppression de votre compte ou d'une entreprise se fait uniquement dans prepza. Ce que l'application lit parvient à son fournisseur, selon les conditions de cette application. Vous pouvez la déconnecter à tout moment dans le même onglet. D'autres applications d'IA et les agents que vous créez vous-même peuvent aussi se connecter : l'[onglet MCP](/api-docs?tab=mcp) de la documentation développeurs donne les étapes et des exemples d'agents, et un agent sur un serveur peut se connecter avec une clé API dotée de l'autorisation pour les agents IA. Le [guide des agents IA, du MCP et des API](/guides/ai-agents-mcp-and-api) explique à quoi sert chacun.",
    },
    {
        "key": "candidates",
        "question": "Que voient les candidats ?",
        "answer": "Le nom et le logo de votre entreprise, aux couleurs et dans la police de votre entreprise (définies dans son onglet Marque), ce qui les attend avant de commencer, puis une question chronométrée à la fois. Ils ne voient jamais leur score ni si une réponse était juste.",
    },
    {
        "key": "verified",
        "question": "Que signifie la coche de vérification ?",
        "answer": "Qu'un propriétaire ou un administrateur de l'entreprise s'est connecté avec un e-mail professionnel sur le site de l'entreprise, comme vous@acme.com, puis que notre équipe a examiné l'entreprise. Ajoutez le site avec Vérifier dans l'en-tête de votre entreprise ; les services d'e-mail gratuits ne comptent pas. Tant que l'examen est en attente, votre équipe voit une horloge à côté du nom, et renommer l'entreprise la renvoie en examen. La coche s'affiche à côté du nom de votre entreprise, y compris dans les invitations.",
    },
    {
        "key": "languages",
        "question": "Quelles langues sont prises en charge ?",
        "answer": "{count} langues, pour le site, les entretiens et les e-mails. Choisissez la langue dans laquelle un entretien est rédigé, quelle que soit la langue de la fiche de poste.",
    },
    {
        "key": "privacy",
        "question": "Que deviennent les fiches de poste et les réponses ?",
        "answer": "Les fiches de poste servent à créer les entretiens de votre entreprise, et les réponses des candidats à les noter pour votre entreprise. Les questions générées par prepza peuvent aussi être réutilisées dans les entretiens et l'entraînement d'autres entreprises, sans rien qui vous identifie, vous, votre entreprise ou toute autre personne ; vous pouvez exclure de cette réutilisation les questions d'un entretien dans ses paramètres. prepza tire aussi des réponses données aux questions des tendances générales et anonymisées sur leur qualité, afin d'améliorer la façon dont les questions sont générées. La [politique de confidentialité](/privacy) explique ce que nous conservons, pendant combien de temps, et les droits de chacun.",
    },
    {
        "key": "eu_ai_law",
        "question": "Est-il légal d'utiliser l'IA pour présélectionner des candidats dans l'UE ?",
        "answer": "Oui, avec des règles. Selon le règlement européen sur l'IA (AI Act), les outils qui notent des candidats sont très probablement à haut risque, avec des obligations à partir du 2 décembre 2027, et le RGPD s'applique déjà : une personne prend la décision d'embauche, les candidats sont informés de l'usage de l'IA et des traces sont conservées. prepza fonctionne ainsi : l'IA rédige les questions, des personnes de votre entreprise examinent les résultats et décident, et les candidats sont informés avant de commencer. Ceci n'est pas un conseil juridique ; [L'IA dans le recrutement est-elle légale dans l'UE ?](/guides/is-ai-hiring-legal-in-the-eu) explique les règles et les dates.",
    },
    {
        "key": "emails",
        "question": "Quels e-mails prepza envoie-t-il, et comment les arrêter ?",
        "answer": "Les e-mails de service, comme les invitations, les rapports, les problèmes de paiement et les modifications de nos conditions, sont toujours envoyés. Les autres, comme le récapitulatif d'activité quotidien, les rappels et les nouveautés du produit, se choisissent dans les Paramètres, sous E-mails, ou s'arrêtent avec le lien « Se désabonner » de chaque e-mail. Les candidats peuvent arrêter les e-mails de votre entreprise, ou les rappels d'un entretien, avec les liens de leurs invitations et rappels. Les actualités de prepza s'affichent dans vos notifications, la cloche en haut ; les plus importantes arrivent aussi par e-mail comme nouveauté du produit, uniquement tant que ce réglage est activé.",
    },
    {
        "key": "delete",
        "question": "Puis-je supprimer mon compte ?",
        "answer": "Oui, dans les Paramètres. Votre compte et vos données sont supprimés, et vous pouvez d'abord télécharger une copie de vos données.",
    },
    {
        "key": "report",
        "question": "Comment signaler un problème ?",
        "answer": "Écrivez-nous depuis la [page de contact](/contact) et collez l'ID de ce qui est concerné : « copier l'id » se trouve sous le nom d'une entreprise, d'un entretien ou d'un candidat, et celui de votre compte dans le menu de votre compte et dans les Paramètres. Avec l'ID, nous le retrouvons aussitôt.",
    },
]
