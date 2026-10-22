---
title: "Agents IA, MCP et API : ce que c'est et comment s'en servir dans le recrutement"
seoTitle: "Agents IA, MCP et API en recrutement : définition et usages"
description: "Agent IA, MCP et API : définitions, usage sûr dans le recrutement et pilotage de prepza depuis son agent, Claude, ChatGPT ou votre plateforme."
updated: "2026-10-21"
---

# Agents IA, MCP et API : ce que c'est et comment s'en servir dans le recrutement

La plupart d'entre nous ont découvert l'IA sous la forme d'une fenêtre de discussion : vous posez une question, elle répond. Un agent IA va un cran plus loin. Il peut chercher des informations dans vos outils et, quand vous le lui demandez, y agir : créer un entretien, inviter une liste de candidats, vous dire qui a obtenu la meilleure note la semaine dernière. Le Model Context Protocol (MCP) est le standard qui permet à l'assistant IA que vous utilisez déjà, comme Claude ou ChatGPT, de se connecter à ce type d'outils. Quant à l'API, c'est le moyen plus ancien et plus précis de faire dialoguer des logiciels entre eux, sans IA au milieu.

Ce guide explique ces trois notions simplement, ce qu'elles apportent au recrutement, les points de vigilance et la façon de les utiliser avec prepza.

## Ce qu'est un agent IA

Un chatbot ne fait qu'écrire du texte. Un agent est un modèle de langage doté d'**outils** : de petites actions bien définies qu'il peut appeler, comme « lister les candidats de cet entretien » ou « inviter cette adresse e-mail ». Quand vous lui demandez quelque chose, l'agent choisit les outils à utiliser, lit ce qu'ils renvoient et répond à partir de ces données, pas de mémoire.

| Un chatbot | Un agent IA |
| --- | --- |
| Répond à partir de ce qu'il a appris à l'entraînement | Répond à partir de vos données à jour, lues via ses outils |
| Peut seulement décrire comment faire quelque chose | Peut le faire, quand vous le demandez et l'autorisez |
| Devine quand il ne sait pas | Vérifie, ou dit qu'il ne peut pas |
| Vit dans une seule fenêtre | Travaille dans les outils auxquels vous le connectez |

Ce sont les outils qui rendent un agent utile, et aussi ce qui le rend sûr ou non. Un bon agent ne peut utiliser que les outils qu'on lui donne, uniquement avec vos permissions, et ne fait que ce que vous avez demandé.

## Ce qu'est MCP

Le Model Context Protocol est un standard ouvert, lancé par Anthropic fin 2024 et désormais pris en charge par Claude, ChatGPT et de nombreuses autres applications d'IA et outils de développement. On le compare souvent à un port USB-C pour l'IA : au lieu que chaque application d'IA construise sa propre connexion à chaque outil, un outil propose un seul **serveur MCP**, et toute application d'IA qui parle MCP peut l'utiliser.

Un serveur MCP indique trois choses à l'application d'IA :

1. **Quels outils existent**, avec un nom, une description et les informations dont chacun a besoin.
2. **Quels outils se contentent de lire** et lesquels modifient quelque chose, pour que l'application d'IA puisse vous demander votre accord avant une modification.
3. **Qui vous êtes**, grâce à une connexion que vous approuvez une seule fois, pour que chaque appel s'exécute en votre nom, avec vos permissions.

Concrètement, vous pouvez travailler avec un outil depuis l'assistant que vous utilisez déjà, sans copier de données d'une fenêtre à l'autre.

## Ce qu'est une API, et en quoi elle diffère

Une API (interface de programmation d'application) est un ensemble de requêtes fixes qu'un programme peut envoyer à un autre : « lister les candidats de cet entretien », « inviter cette adresse e-mail ». Vos développeurs écrivent le code qui les envoie. Aucune IA n'intervient : la même requête produit toujours le même résultat, et c'est exactement ce qu'on attend d'une automatisation qui tourne seule.

| | Agent IA (dans l'application) | MCP (dans Claude ou ChatGPT) | API |
| --- | --- | --- | --- |
| Qui l'utilise | Vous, dans prepza | Vous, dans votre assistant IA | Le code de votre plateforme |
| Comment demander | Avec vos propres mots | Avec vos propres mots | Des requêtes fixes écrites par un développeur |
| Qui approuve les modifications | Vous, sur une carte | Vous, dans votre application d'IA | Votre code, tel qu'il est écrit |
| Idéal pour | Questions et tâches rapides | Combiner prepza avec vos autres outils et fichiers | Une automatisation qui tourne sans surveillance |
| Se connecte en tant que | Vous | Vous | Une clé d'entreprise |

Utilisez un agent ou MCP quand une personne garde la main. Utilisez l'API quand votre propre système doit inviter les candidats et récupérer les résultats tout seul, par exemple depuis un site carrières ou un outil RH interne.

## À quoi cela sert dans le recrutement

Le recrutement comporte beaucoup de petites étapes répétitives, réparties entre plusieurs outils. C'est précisément là qu'un agent excelle :

- **Des questions sur votre pipeline.** « Quels candidats pour Senior Backend ont réussi cette semaine ? », « Qui n'a pas encore commencé son entretien ? », « Quelle est notre note moyenne pour le poste de data analyst ? »
- **La configuration.** « Crée un entretien à partir de cette fiche de poste », « Mets le seuil de réussite à 70 % », « Accorde 50 % de temps supplémentaire à ce candidat. »
- **Les actions en masse.** « Invite ces 12 personnes à l'entretien frontend », collé directement depuis un e-mail ou un tableur.
- **Le croisement des sources.** Dans Claude ou ChatGPT, vous pouvez combiner prepza avec vos autres outils et fichiers connectés : comparer une fiche de poste de vos documents avec les thèmes de l'entretien, ou rédiger un message aux candidats présélectionnés.

Ce qu'il ne doit pas faire, c'est prendre la décision d'embauche. Une note éclaire le jugement d'une personne ; elle ne le remplace pas. Demandez à l'agent de trier, résumer et préparer, et laissez la décision à une personne. Lisez [L'IA dans le recrutement est-elle légale dans l'UE ?](/guides/is-ai-hiring-legal-in-the-eu) pour comprendre pourquoi c'est aussi important sur le plan juridique.

## Les points de vigilance

Connecter une IA à vos données de recrutement mérite le même soin que donner un accès à un collègue.

| Risque | Ce qui aide |
| --- | --- |
| L'agent fait quelque chose que vous ne vouliez pas | Les modifications demandent d'abord votre accord, et il ne fait que ce que vous avez demandé |
| Il voit plus qu'il ne devrait | Il agit en votre nom : il voit ce que vous voyez, rien de plus |
| Des instructions cachées dans les données | Les noms, réponses et documents des candidats sont des données, jamais des instructions à suivre |
| Des secrets qui finissent dans une conversation | Les clés API et les mots de passe ne passent jamais par la conversation |
| Des erreurs irréversibles | La suppression d'un compte ou d'une entreprise reste dans l'application, derrière sa propre confirmation |
| Des données qui quittent vos outils | Les données parviennent à l'application d'IA que vous connectez, selon les conditions de cette application : ne connectez que des applications autorisées par votre entreprise |
| Un usage qui s'emballe | Des limites sur le nombre d'actions exécutées par heure |

Avant de connecter une application d'IA à des données professionnelles, vérifiez la politique de votre entreprise sur les outils d'IA, et indiquez aux candidats, dans votre politique de confidentialité, quels services traitent leurs données.

## Trois façons d'utiliser prepza au-delà de ses pages

### 1. L'agent intégré

Sélectionnez **demander à l'agent** dans l'en-tête de n'importe quelle page. L'agent connaît vos entreprises, entretiens, candidats, crédits et intégrations, ainsi que le fonctionnement de prepza. Il répond dans votre langue, et vous pouvez écrire ou parler.

- **Il répond à partir de vos données**, avec la même vue que vous : un admin voit ce que voit un admin, un lecteur ce que voit un lecteur.
- **Il sait sur quelle page vous êtes.** Demandez « Que puis-je faire sur cette page ? » pour obtenir le guide de cette page, ou « Qui est le meilleur ici ? » sur les candidats d'un entretien, et il répond sur cet entretien sans vous demander lequel.
- **Il prépare les modifications, vous les confirmez.** Si vous lui demandez d'inviter des candidats, il affiche une carte qui montre exactement ce qui va se passer, par exemple « Inviter 12 candidats à Backend developer ». Rien ne s'exécute tant que vous n'avez pas sélectionné Confirmer.
- **Il montre ses sources.** Sous une réponse, vous trouvez les candidats ou entretiens qu'il a utilisés et un lien vers la page d'où ils viennent.
- **Il reste dans son sujet.** Il répond sur prepza et sur le recrutement avec prepza, et décline le reste.

### 2. prepza dans Claude ou ChatGPT, via MCP

Si votre équipe travaille déjà dans Claude ou ChatGPT, vous pouvez y faire venir prepza. Le serveur MCP de prepza propose les mêmes outils que l'agent intégré.

**Pour vous connecter :**

1. Dans prepza, ouvrez l'onglet **Intégrations** d'une entreprise et sélectionnez **Apps IA**. Copiez l'adresse du serveur : `https://prepza.ai/mcp`.
2. **Dans Claude :** ouvrez les paramètres, puis Connecteurs, et ajoutez un connecteur personnalisé avec cette adresse. **Dans Claude Code :** exécutez `claude mcp add --transport http prepza https://prepza.ai/mcp`. **Dans ChatGPT :** ajoutez-le comme connecteur personnalisé dans ses paramètres d'applications et de connecteurs.
3. Votre application d'IA ouvre la page de connexion de prepza. Connectez-vous, vérifiez quelle application fait la demande et sélectionnez **Autoriser**. Pour qu'elle puisse seulement lire, désactivez d'abord **Autoriser les modifications**.

Ensuite, posez vos questions dans la conversation comme vous le feriez à un collègue : « Dans prepza, quels sont les trois meilleurs candidats pour Product designer ? » La plupart des applications d'IA vous demandent votre accord avant une modification et vous avertissent avant toute action irréversible : prepza leur indique quelles actions modifient ou suppriment quelque chose.

**Ce qui reste identique à l'application :**

- **Vos permissions.** Il agit en votre nom, dans chaque entreprise dont vous êtes membre, avec votre rôle dans chacune.
- **Crédits et limites.** Inviter un candidat coûte la même chose que dans l'application, et les mêmes limites d'e-mails s'appliquent.
- **La traçabilité.** Tout ce qu'une app d'IA fait pour vous apparaît dans le journal des actions de l'entreprise comme fait via une app d'IA, de la validation des thèmes et la consultation des résultats à l'octroi de temps supplémentaire ou la révocation d'un candidat. Le propriétaire de l'entreprise le consulte dans l'onglet **Journal des actions** de l'entreprise.
- **L'entreprise décide.** Les propriétaires et administrateurs peuvent empêcher les apps d'IA d'utiliser les données d'une entreprise avec **Autoriser les apps d'IA dans cette entreprise** sur sa page des apps d'IA.
- **Ce qu'il ne peut pas faire.** Il ne peut pas voir votre mot de passe ni vos clés API, et il ne peut pas supprimer votre compte ni une entreprise. Ces actions restent dans l'application.

**Pour vous déconnecter,** supprimez le connecteur dans votre application d'IA, ou sélectionnez **Déconnecter** à côté de celui-ci sous **Apps IA**, dans l'onglet Intégrations. Il cesse de fonctionner immédiatement.

**Autres applications et vos propres agents.** L'[onglet MCP](/api-docs?tab=mcp) de la documentation développeurs donne les étapes pour Gemini CLI, Cursor, VS Code et Le Chat, ainsi que des exemples complets d'agents en Python et TypeScript. Un agent qui tourne sur un serveur, sans personne pour approuver une connexion, utilise une clé API de l'entreprise avec l'autorisation **Utiliser avec des agents IA (MCP)** : il ne fonctionne que dans cette entreprise, et seulement avec les outils que permettent les autres autorisations de la clé.

### 3. Votre propre plateforme, via l'API

Pour une automatisation sans IA, prepza propose une API, décrite dans sa [documentation développeurs](/api-docs).

1. Un propriétaire ou un admin ouvre l'onglet **Intégrations** d'une entreprise, puis **API**, et sélectionne **Nouvelle clé**. Donnez-lui le nom de la plateforme qui l'utilisera, choisissez sa date d'expiration et cochez uniquement ce dont elle a besoin : la clé d'un tableau de bord ne fait que lire, celle d'un site carrières invite aussi. Vous pourrez retirer des autorisations plus tard, jamais en ajouter. La clé ne s'affiche qu'une fois ; conservez-la en lieu sûr.
2. Votre plateforme envoie des requêtes avec cette clé : lister les entretiens de l'entreprise, lister ou consulter les candidats avec leur note, s'ils ont réussi et leurs alertes d'intégrité, et inviter un candidat.
3. Ajoutez un **webhook** : une adresse sur votre plateforme que prepza appelle, avec une signature, quand un candidat commence, termine ou est retiré, quand son invitation n'a pas pu lui parvenir ou a expiré, et quand un entretien est prêt, pour ne pas avoir à demander sans cesse. La page API peut lui envoyer un événement de test et affiche son journal des envois.

Chaque candidat est accompagné d'un lien vers ses résultats complets dans prepza et, tant qu'il n'a pas terminé, de son propre lien d'invitation, pour que votre plateforme puisse l'envoyer dans son propre message si vous préférez. Quand votre plateforme sait déjà qui est le candidat, invitez-le sans connexion : prepza n'envoie aucun e-mail, et le candidat passe l'entretien depuis le lien sans se connecter à prepza, alors n'envoyez ce lien qu'à lui. Une invitation peut aussi ramener le candidat sur votre site grâce à un bouton sur la page de fin, et définir un thème clair ou sombre aux couleurs de votre entreprise. Avec le SDK de prepza, votre propre page peut afficher l'entretien lui-même. Ramener les candidats sur votre site et y afficher l'entretien nécessitent une entreprise vérifiée, et ne fonctionnent que sur le domaine de son site web.

La règle reste la même que partout ailleurs : la note éclaire la décision d'une personne, alors ne refusez pas de candidats automatiquement sur cette base.

## Lequel utiliser, et quand

Partez de qui fait le travail et à quelle fréquence.

| Votre situation | À utiliser |
| --- | --- |
| Vous êtes dans prepza et voulez une réponse rapide : qui a réussi, qui n'a pas commencé, combien de crédits il reste | L'agent intégré |
| Vous voulez configurer quelque chose en quelques mots : un entretien à partir d'une fiche de poste, un seuil de réussite, du temps supplémentaire | L'agent intégré |
| Vous travaillez déjà toute la journée dans Claude ou ChatGPT et voulez y retrouver prepza | MCP |
| La tâche demande prepza et autre chose : vos documents, des brouillons d'e-mails, un autre outil connecté | MCP |
| Un recruteur en déplacement veut suivre le pipeline depuis l'application d'IA de son téléphone | MCP |
| Votre site carrières ou votre système RH doit inviter les candidats tout seul, sans que personne ne clique | L'API |
| Les résultats doivent arriver dans votre propre base de données ou tableau de bord dès que les candidats ont terminé | L'API, avec un webhook |
| Votre ATS fait partie de ceux auxquels prepza se connecte (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Aucun des trois : connectez l'ATS dans l'onglet Intégrations. Voir [Comment connecter vos tests de compétences à votre ATS](/guides/ats-integration-skills-tests) |

Une règle simple :

- **Une personne demande et vérifie chaque modification :** l'agent dans prepza, ou MCP si cette personne passe ses journées dans Claude ou ChatGPT.
- **Un logiciel agit seul, toujours de la même façon :** l'API.
- **Pour commencer :** essayez d'abord l'agent intégré. Il ne demande aucune configuration, et ce que vous apprenez vous servira avec MCP.

Ils fonctionnent aussi ensemble. Une équipe peut envoyer les invitations depuis son système RH via l'API, pendant que les recruteurs interrogent l'agent ou leur assistant IA sur les résultats.

## Obtenir de bons résultats

- **Nommez les choses.** « L'entretien Senior Backend » fonctionne mieux que « cet entretien ».
- **Demandez une étape à la fois** quand l'enjeu est important. Vérifiez le résultat, puis demandez la suite.
- **Lisez la demande d'accord avant de l'accepter.** Elle montre exactement ce qui va s'exécuter.
- **Demandez d'où vient un chiffre.** Un bon agent peut indiquer les candidats ou la page sur lesquels il s'appuie.
- **Laissez les décisions aux humains.** Utilisez l'agent pour trouver, trier et préparer ; décidez vous-même.

## Tarifs

L'agent intégré, la connexion MCP et l'API sont gratuits. Vous ne payez que les candidats, comme toujours : par candidat qui répond à au moins une question, sans abonnement. Voir les [tarifs](/pricing).

## À lire aussi

- [Comment connecter vos tests de compétences à votre ATS](/guides/ats-integration-skills-tests)
- [Recruter des développeurs à l'ère de l'IA](/guides/interviewing-in-the-age-of-ai)
- [L'IA dans le recrutement est-elle légale dans l'UE ?](/guides/is-ai-hiring-legal-in-the-eu)
