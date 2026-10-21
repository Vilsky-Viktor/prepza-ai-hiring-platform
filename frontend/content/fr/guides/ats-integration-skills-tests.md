---
title: "Comment connecter vos tests de compétences à votre ATS"
seoTitle: "Connecter ses tests de compétences à son ATS : le guide"
description: "Envoyez les tests de compétences et recevez les résultats dans votre ATS automatiquement, laissez décider les humains et sachez quoi vérifier d'abord."
updated: "2026-10-21"
---

# Comment connecter vos tests de compétences à votre ATS

La plupart des équipes de recrutement gèrent les candidats dans un logiciel de suivi des candidatures (ATS) et font passer les tests de compétences dans un autre outil. Sans lien entre les deux, quelqu'un copie les e-mails depuis l'ATS, envoie les invitations à la main, attend, puis recopie les scores. Avec cinq candidats, ça passe. Avec cinquante, les invitations partent en retard, les résultats dorment dans un deuxième onglet que personne n'ouvre, et de bons candidats acceptent d'autres offres pendant qu'ils attendent.

Ce guide explique ce que fait une bonne connexion entre un ATS et un outil de test, ce qu'il faut vérifier avant de s'y fier et comment la configurer pour que l'automatisation prenne en charge les tâches répétitives tandis que des humains prennent toujours chaque décision de recrutement.

## Pourquoi les connecter

| Sans connexion | Avec connexion |
| --- | --- |
| Quelqu'un exporte ou copie les e-mails des candidats | Déplacer un candidat vers une étape envoie l'invitation |
| Les invitations partent quand quelqu'un a le temps | Les invitations partent quelques minutes après le déplacement |
| Les résultats restent dans l'outil de test | Les résultats apparaissent sur la fiche du candidat dans l'ATS |
| Les managers demandent « quelqu'un l'a-t-il déjà testé ? » | L'ATS montre qui a été testé et avec quel résultat |
| Des fautes de frappe dans les e-mails et des candidats oubliés | L'ATS est la seule liste de ceux qui ont postulé |

La rapidité compte plus qu'il n'y paraît. Plus le délai entre la candidature et la réponse est long, plus les candidats abandonnent ou acceptent un autre poste. Les taux d'abandon exacts varient beaucoup selon le poste et le marché, prenez donc les chiffres publiés avec prudence, mais la tendance est constante : un processus lent perd des candidats, et les meilleurs sont généralement ceux qui ont le plus d'options.

## À quoi ressemble un bon flux

Une bonne intégration suit les étapes que vous utilisez déjà. Elle n'invente pas de nouveau processus.

1. **Un candidat postule** et arrive dans votre ATS comme d'habitude.
2. **Une personne le déplace vers une étape de test,** par exemple « Test de compétences ». Ce déplacement est le déclencheur : c'est donc toujours un humain qui décide qui passe le test.
3. **L'outil de test envoie l'invitation** automatiquement, pour le test lié à ce poste.
4. **Le candidat passe le test** quand cela lui convient, dans le délai que vous fixez.
5. **Les résultats sont inscrits sur le candidat dans l'ATS :** le score, s'il a réussi, les alertes d'intégrité et un lien vers toutes ses réponses.
6. **Une personne examine le résultat** et fait avancer le candidat, ou non.

Deux choses restent manuelles, volontairement : choisir qui passe le test et décider de la suite. La connexion supprime seulement les copier-coller entre les deux.

### Pourquoi ne pas déclencher à chaque nouvelle candidature ?

Certains outils invitent toutes les personnes qui postulent. Cela peut convenir aux postes à fort volume où tous les candidats passent le même test. Mais une étape vers laquelle vous déplacez les candidats se contrôle plus facilement : vous pouvez écarter ceux qui ne remplissent clairement pas une exigence éliminatoire (pas de permis de travail, mauvaise localisation), et vous ne testez jamais, ni ne payez, quelqu'un que vous alliez de toute façon refuser.

## Ce qu'il faut vérifier avant de choisir une intégration

Toutes les promesses du type « s'intègre à votre ATS » ne se valent pas. Posez ces questions avant de connecter quoi que ce soit.

| Question | Pourquoi c'est important | Une bonne réponse |
| --- | --- | --- |
| Comment se fait la connexion ? | Les mots de passe partagés et les comptes détenus par l'éditeur sont difficiles à auditer ou à révoquer | Une clé API ou un jeton que votre entreprise crée et peut supprimer à tout moment |
| Que peut faire la clé ? | Une clé avec un accès complet est un risque si elle fuite | Les permissions minimales dont l'intégration a besoin, listées dans la documentation |
| Qu'est-ce qui déclenche une invitation ? | Vous devez savoir exactement quand les candidats reçoivent un e-mail | Une étape précise que vous choisissez, poste par poste |
| Où arrivent les résultats ? | Des résultats que personne ne voit ne servent à rien | Sur le profil du candidat, sous forme de note ou de commentaire que votre équipe lit déjà |
| Que se passe-t-il si une invitation échoue ? | Plus de crédits, une faute de frappe, un compte en pause : des candidats bloqués sans que personne ne le sache | Quelqu'un est prévenu, et le candidat peut être invité à nouveau |
| Un événement peut-il être traité deux fois ? | Les ATS renvoient des événements ; un candidat ne doit pas recevoir deux invitations | Chaque candidat est invité une seule fois par test, quel que soit le nombre de fois où l'événement arrive |
| Comment les événements entrants sont-ils vérifiés ? | On peut envoyer de faux événements à une adresse non vérifiée | Des requêtes signées que l'outil vérifie |
| Combien de temps les données des candidats sont-elles conservées ? | Les lois sur la vie privée comme le RGPD attendent une durée de conservation claire | Une limite annoncée, et la suppression quand vous supprimez le poste, le test ou votre compte |
| Combien ça coûte ? | Les tarifs par utilisateur peuvent rendre l'automatisation coûteuse | Un coût prévisible par candidat testé |

Si l'éditeur ne sait pas répondre clairement aux questions sur les échecs et les doublons, attendez-vous à le découvrir à vos dépens.

### Protection des données

Connecter deux systèmes, c'est faire circuler des données de candidats, au minimum des noms et des e-mails, entre deux entreprises. Selon le RGPD et les lois similaires, votre éditeur de tests est généralement votre sous-traitant : il vous faut un accord de traitement des données (DPA), et vous devez indiquer aux candidats, dans votre politique de confidentialité ou dans l'invitation, qu'un test de compétences fait partie du processus. Ne transmettez que les données dont le test a besoin. Pour en savoir plus sur l'aspect juridique des tests et de l'IA dans le recrutement, lisez [L'IA dans le recrutement est-elle légale dans l'UE ?](/guides/is-ai-hiring-legal-in-the-eu)

## Liste de contrôle pour la configuration

Avant de l'activer pour un vrai poste :

1. **Créez dans votre ATS une étape réservée au test,** comme « Test de compétences ». Ne réutilisez pas une étape qui signifie autre chose, sinon des candidats seront invités par erreur.
2. **Créez la clé depuis un compte administrateur** qui voit tous les postes que vous voulez lier, avec uniquement les permissions indiquées dans la documentation.
3. **Liez chaque poste à son test** et choisissez l'étape qui déclenche l'invitation.
4. **Configurez le webhook** si votre ATS vous demande de le faire à la main, et collez son secret là où l'outil le demande.
5. **Testez avec vous-même.** Ajoutez un candidat avec votre propre e-mail, déplacez-le vers l'étape, passez le test et vérifiez que la note apparaît dans l'ATS.
6. **Décidez qui surveille les échecs :** qui est prévenu quand une invitation ne peut pas partir, et qui règle le problème.
7. **Mettez-vous d'accord sur la lecture des résultats.** Un seuil de réussite est un repère, pas un refus automatique. Décidez-le avant l'arrivée des résultats, pas après.

## Erreurs fréquentes

- **Automatiser la décision au lieu des tâches administratives.** Refuser automatiquement tous ceux qui sont sous un certain score supprime le contrôle humain qui repère une mauvaise question ou un candidat qui a eu un problème de connexion. Laissez le score trier ; laissez une personne décider.
- **Déclencher depuis la mauvaise étape.** Une étape que les recruteurs utilisent pour d'autres raisons envoie des tests à des personnes qui ne devraient pas les recevoir.
- **Un seul test pour tous les postes.** La connexion permet d'envoyer facilement le même test partout. Un test est le plus utile quand il est conçu pour le poste concerné. Voir [Tests de compétences ou tri de CV](/guides/skills-tests-vs-cv-screening).
- **Personne ne surveille les échecs.** Si une invitation échoue en silence, le candidat attend un e-mail qui n'arrive jamais, et vous pensez qu'il l'a ignoré.
- **Une clé liée à quelqu'un qui part.** Certaines clés d'ATS agissent au nom de la personne qui les a créées. Quand son compte est fermé, la connexion s'arrête. Utilisez un compte qui restera, et reconnectez quand les personnes changent de rôle.
- **Oublier les candidats hors de l'ATS.** Les cooptations et les candidatures directes qui n'entrent jamais dans l'ATS ont aussi besoin d'une invitation. Gardez aussi un moyen de les inviter à la main.

## Comment prepza s'y prend

prepza se connecte à **Workable, Greenhouse, Teamtailor, Recruitee et Breezy HR** et suit le flux décrit ci-dessus.

- **Votre clé, votre contrôle.** Un propriétaire ou un admin connecte l'ATS dans l'onglet Intégrations de l'entreprise avec une clé que votre entreprise crée dans l'ATS. prepza la vérifie avant de l'enregistrer, la stocke chiffrée et ne l'affiche plus jamais. La déconnexion supprime immédiatement la clé et les postes liés.
- **Lier un poste à un entretien.** Choisissez un poste de l'ATS et l'étape qui déclenche l'invitation, puis liez-le à un entretien prepza existant ou créez-en un à partir du texte du poste dans l'ATS. Vous validez les thèmes avant qu'une seule question soit rédigée.
- **Vous déplacez un candidat, l'invitation part.** Chaque candidat est invité une seule fois par entretien, même si l'ATS envoie deux fois le même événement.
- **Les résultats reviennent dans l'ATS.** Quand un candidat a terminé, prepza lui ajoute dans l'ATS une note ou un commentaire avec son résultat, s'il a réussi, les alertes d'intégrité (sortie de la page, tentatives de copie, réponses choisies trop vite pour avoir lu la question) et un lien vers sa fiche d'évaluation avec toutes ses réponses.
- **Les échecs ne passent pas inaperçus.** Si un candidat ne peut pas être invité, par exemple parce que l'entreprise n'a plus de crédits, a atteint une limite d'e-mails, ou parce que prepza a mis les invitations en pause temporairement, tous les membres de l'entreprise reçoivent une notification qui nomme l'ATS. Les candidats non invités faute de crédits sont invités automatiquement après une recharge, et les candidats en attente de n'importe quel poste peuvent être réinvités en un clic.
- **Slack, si vous l'utilisez.** prepza peut publier des notifications, comme un candidat qui a terminé ou un candidat de l'ATS qui n'a pas pu être invité, dans le canal Slack de votre choix.
- **Votre propre plateforme.** Si votre ATS ne figure pas dans la liste, l'[API](/api-docs) de prepza vous permet d'inviter des candidats avec une clé API et de recevoir un webhook signé quand un candidat commence, termine ou est retiré, quand son invitation n'a pas pu lui parvenir ou a expiré, et quand un entretien est prêt.
- **Des données conservées pour une durée fixe.** Les candidats issus d'un ATS sont supprimés au bout de 365 jours, ou plus tôt avec leur entretien ou leur entreprise.

Certains ATS demandent une étape de leur côté. Greenhouse, Teamtailor et Recruitee vous demandent d'ajouter un webhook à la main ; la fenêtre Instructions de prepza indique l'adresse et où coller son secret. prepza configure lui-même les webhooks de Workable et de Breezy HR.

La tarification se fait par candidat, sans abonnement : vous ne payez que pour les candidats qui répondent à au moins une question, 5 $ chacun avec la recharge de 50 $, 4 $ à partir d'une recharge de 200 $, 3 $ à partir d'une recharge de 600 $ et 2 $ à partir d'une recharge de 1 000 $. Les prix sont ici en dollars américains, et dans la devise locale au Canada, en Australie, en Israël, en Pologne, en Suisse, au Japon, en Corée du Sud, à Taïwan, à Hong Kong, en Thaïlande, à Singapour, en Inde, dans le reste de l'Europe et au Royaume-Uni ; la TVA ou la sales tax est gérée au moment du paiement. Connecter un ATS et créer des entretiens est gratuit, et les 3 premiers candidats de votre première entreprise sont gratuits. Voir les [tarifs](/pricing).

## À lire aussi

- [Comment présélectionner 100 candidats en une journée](/guides/screen-100-applicants-in-a-day)
- [Tests de compétences ou tri de CV](/guides/skills-tests-vs-cv-screening)
- [Tests de recrutement : guide pratique](/pre-employment-testing)
