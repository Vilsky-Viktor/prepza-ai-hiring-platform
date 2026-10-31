# The FAQ in pt; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "O que é a testee?",
        "answer": "Uma entrevista cronometrada criada a partir da sua descrição de vaga, para qualquer cargo. Use-a para fazer a triagem de candidatos antes de conhecê-los ou como uma etapa da própria contratação: de qualquer forma, você vê quem realmente conhece o trabalho.",
    },
    {
        "key": "roles",
        "question": "Para quais cargos posso contratar?",
        "answer": "Qualquer cargo em que o conhecimento importa: suporte, vendas, finanças, saúde, ofícios técnicos, engenharia, marketing e muito mais. Se você consegue descrever o trabalho, a testee consegue criar uma entrevista para ele.",
    },
    {
        "key": "hiring",
        "question": "Como funciona?",
        "answer": "Cole uma descrição de vaga na página inicial, informe o nome da sua empresa e confira os tópicos que a testee propõe. Depois, convide candidatos: digite os e-mails, cole uma lista ou envie um arquivo. Candidatos que não começaram depois de alguns dias recebem um lembrete. Cada candidato recebe suas próprias questões, com um cronômetro em cada uma, e você vê a pontuação e todas as respostas assim que ele termina.",
    },
    {
        "key": "link",
        "question": "Posso colocar uma entrevista em um anúncio de vaga?",
        "answer": "Sim. Ative o link compartilhável da entrevista na aba Configurações e cole-o no seu anúncio. Quem o abre entra na conta e faz a entrevista, e cada pessoa é cobrada como um candidato convidado. O link é desativado quando você marca a entrevista como “Contratado”.",
    },
    {
        "key": "preview",
        "question": "Posso experimentar uma entrevista antes de convidar alguém?",
        "answer": "Sim. Abra sua entrevista como candidato na página dela, sem custo: as prévias não aparecem entre seus candidatos nem nas estatísticas das questões. Você também pode fazer qualquer uma das simulações de entrevista gratuitas.",
    },
    {
        "key": "open-to-offers",
        "question": "As empresas podem me encontrar pela minha prática?",
        "answer": "Só se você quiser. Ative Aberto a propostas depois de uma rodada de prática ou em Configurações, com o endereço do seu perfil do LinkedIn. As empresas que contratam pela testee passam a ver seu nome, seu perfil do LinkedIn e seu resultado de prática mais recente em cada tema das entrevistas delas que você praticou, e podem convidar você para uma entrevista. A testee não classifica nem recomenda você. Desative quando quiser em Configurações, e você some na hora da lista de todas as empresas; a opção também termina um ano depois da última vez que você a ativou ou salvou seu perfil do LinkedIn.",
    },
    {
        "key": "cheating",
        "question": "Os candidatos podem usar IA ou procurar as respostas?",
        "answer": "Cada candidato recebe suas próprias questões aleatórias, em sua própria ordem, com [um cronômetro em cada questão](/guides/skills-test-timing-and-extra-time) controlado pelo nosso servidor, então sobra pouco tempo para procurar respostas ou perguntar a uma IA. Os resultados também mostram quando um candidato saiu da página, copiou texto ou respondeu rápido demais para ter lido a questão. Quando ele termina, a página do candidato também aponta padrões de resposta que costumam aparecer quando alguém repassa as questões a uma IA, como mais ou menos o mesmo tempo em cada questão ou questões difíceis certas enquanto as fáceis estavam erradas, e sugere questões que ele acertou para explorar em uma entrevista ao vivo. Um padrão é um motivo para perguntar, não uma prova. Antes de começar, cada candidato também confirma que vai responder por conta própria, sem ferramentas de IA nem ajuda de outras pessoas, e os resultados mostram isso.",
    },
    {
        "key": "voice",
        "question": "Os candidatos podem responder por voz?",
        "answer": "Sim, se a empresa definir uma entrevista no modo de voz (em inglês, espanhol, alemão, francês, português ou italiano). As questões são lidas em voz alta e os candidatos respondem falando; o que eles dizem é convertido em texto e associado a uma opção, e nunca é armazenado. As vozes não são analisadas quanto a tom ou emoção, e os candidatos sempre podem tocar em uma opção.",
    },
    {
        "key": "cost",
        "question": "Quanto custa?",
        "answer": "Gerar entrevistas é grátis. Cada candidato que responde pelo menos uma questão custa {candidate} créditos ({candidate_price}), e menos com créditos de recargas maiores, até {cheapest_price}. Sua primeira empresa recebe {company} créditos grátis, o suficiente para os primeiros {company_candidates} candidatos. A [página de preços](/pricing) lista todos os valores.",
    },
    {
        "key": "charged",
        "question": "Quando um candidato é cobrado?",
        "answer": "Desde que ele tenha respondido a pelo menos uma pergunta: quando a entrevista dele termina (ele a conclui ou o tempo acaba enquanto ele está ausente) ou quando você o revoga. Uma pergunta cujo tempo acabou sem resposta escolhida não conta. Os créditos dele são reservados quando você o convida e voltam se você o revogar antes que ele responda a qualquer coisa, se ele nunca começar ou se a entrevista dele terminar sem nenhuma resposta.",
    },
    {
        "key": "compare_hiring",
        "question": "Como o preço se compara a outras ferramentas de avaliação?",
        "answer": "Muitas ferramentas de avaliação são vendidas como assinatura mensal ou anual, paga mesmo que você não avalie ninguém. Na testee você paga só por candidato: {candidate} créditos ({candidate_price}), sem contrato, sem taxa por usuário e sem pagar para gerar uma entrevista. Uma empresa que convida {example_candidates} candidatos por mês paga cerca de {example_year_price} por ano. Se você avalia muitos candidatos todo mês, uma assinatura pode custar menos, então compare com os seus números.",
    },
    {
        "key": "expire",
        "question": "Os créditos expiram?",
        "answer": "Não. Os créditos nunca expiram, e não há assinaturas pagas. Se você ativar a recarga automática opcional, a Paddle salva seu cartão como uma assinatura de {zero_price}; você paga só pelas recargas que ela fizer. Para ativá-la, você mesmo precisa marcar a caixa com o que ela cobra e quando; cada cobrança é enviada por e-mail aos proprietários e administradores da empresa, e você pode desativá-la a qualquer momento onde a ativou, o que a interrompe na hora.",
    },
    {
        "key": "currency",
        "question": "Em que moeda eu pago?",
        "answer": "Os preços são na moeda local no Canadá, na Austrália, em Israel, na Polônia, na Suíça, no Japão, na Coreia do Sul, em Taiwan, em Hong Kong, na Tailândia, em Singapura e na Índia; em euros no restante da UE e na Islândia, em Liechtenstein e na Noruega; em libras no Reino Unido; e em dólares americanos nos demais lugares. Sua conta e cada empresa mantêm a moeda do país em que foram criadas, para onde quer que você viaje: altere a sua em Configurações, e a de uma empresa ao lado do botão Recarregar dela (proprietários e administradores). As recargas de uma empresa, inclusive as automáticas, são sempre cobradas na moeda da empresa.",
    },
    {
        "key": "refunds",
        "question": "Posso pedir reembolso?",
        "answer": "Sim, dos créditos que você comprou nos últimos 14 dias e ainda não gastou: pelo Paddle ou escrevendo para nós. Créditos grátis, como o presente de boas-vindas, não são reembolsados. Os [termos](/terms) têm os detalhes.",
    },
    {
        "key": "scorecards",
        "question": "O que as fichas de avaliação mostram?",
        "answer": 'Cada resposta, se estava certa e quanto tempo levou. A nota é a porcentagem de pontos obtidos: cada pergunta vale um ponto, e uma de "selecionar todas as corretas" dá uma parte dele por opção correta marcada, e nada se uma errada for marcada. As notas aparecem em verde ou vermelho de acordo com a nota de aprovação que você definiu para a entrevista. As fichas também sinalizam respostas rápidas demais para a questão ter sido lida, as vezes que o candidato saiu da página e tentativas de cópia.',
    },
    {
        "key": "reports",
        "question": "Posso compartilhar os resultados com um gestor contratante?",
        "answer": "Sim. Baixe um relatório em PDF de um candidato ou de todos os candidatos de uma entrevista, envie-o por e-mail direto da testee ou mande um resumo curto pelo WhatsApp, Telegram, Viber ou LINE.",
    },
    {
        "key": "action_log",
        "question": "Posso ver quem fez o quê na minha empresa?",
        "answer": "Sim, se você for o proprietário da empresa. A aba Registro de ações dela lista tudo o que os membros fizeram, do mais recente ao mais antigo: convidar ou remover candidatos, ver resultados e alterar as entrevistas, a equipe, o faturamento e as integrações, com quem fez, quando e se o assistente, um app de IA ou a API fez isso em nome da pessoa. Você pode filtrar por membro, tipo de ação e datas. As ações ficam guardadas por 12 meses. As ações de uma chave de API aparecem com o nome da chave. Ali o proprietário também pode baixar uma exportação para auditoria de viés: um arquivo CSV com cada candidato que terminou, com a nota e se foi aprovado, para uma auditoria de viés independente.",
    },
    {
        "key": "notes",
        "question": "Minha equipe pode fazer anotações sobre uma entrevista?",
        "answer": "Sim. Cada entrevista tem uma aba Anotações onde sua equipe escreve anotações em texto simples sobre o processo seletivo, como quem chamar em seguida ou, para uma agência, para qual cliente é a entrevista. Qualquer membro pode escrever anotações, inclusive visualizadores, e editar as suas; o autor, os proprietários e os administradores podem excluir uma. Proprietários e administradores podem fixar uma anotação, que então aparece abaixo do nome da entrevista. Os candidatos nunca veem as anotações.",
    },
    {
        "key": "integrations",
        "question": "A testee funciona com meu ATS ou outras ferramentas?",
        "answer": "Sim, sem custo extra. Conecte Workable, Greenhouse, Teamtailor, Recruitee ou Breezy HR na aba Integrações da sua empresa: os candidatos que você move para uma etapa recebem a entrevista, e os resultados voltam para o ATS ([como integrar testes de habilidades ao seu ATS](/guides/ats-integration-skills-tests)). O Slack pode publicar as notificações da sua empresa em um canal, e a API permite que sua própria plataforma crie entrevistas, convide e gerencie candidatos e receba os resultados deles, com cada chave de API limitada ao que você marcar para ela; veja a [Documentação da API](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "Posso usar a testee pelo Claude, pelo ChatGPT ou pelo meu próprio agente de IA?",
        "answer": "Sim. Adicione a testee ao Claude ou ao ChatGPT como conector (os passos estão na aba Integrações da sua empresa) e permita o acesso na testee. O app passa a trabalhar com suas empresas, entrevistas e os resultados dos candidatos em seu nome, com suas permissões; a maioria dos apps pergunta antes de alterar qualquer coisa. Sua conta ou uma empresa só podem ser excluídas na testee. O que o app lê chega ao fornecedor dele, de acordo com os termos desse app. Você pode desconectá-lo a qualquer momento na mesma aba. Outros apps de IA e agentes que você mesmo cria também se conectam: a [aba MCP](/api-docs?tab=mcp) da documentação para desenvolvedores traz os passos e agentes de exemplo, e um agente em um servidor pode entrar com uma chave de API que tenha a permissão para agentes de IA. O [guia sobre agentes de IA, MCP e APIs](/guides/ai-agents-mcp-and-api) explica para que serve cada um.",
    },
    {
        "key": "candidates",
        "question": "O que os candidatos veem?",
        "answer": "O nome e o logotipo da sua empresa, nas cores e nas fontes da sua empresa (definidas na aba Marca), o que esperar antes de começar e depois uma questão cronometrada por vez. Eles nunca veem a própria pontuação nem se uma resposta estava certa.",
    },
    {
        "key": "verified",
        "question": "O que significa o selo de verificação?",
        "answer": "Que um proprietário ou administrador da empresa entrou com um e-mail corporativo do site da empresa, como you@acme.com, e que depois a nossa equipe analisou a empresa. Adicione o site em Verificar, no cabeçalho da sua empresa; serviços de e-mail gratuitos não contam. Enquanto a análise está pendente, sua equipe vê um relógio ao lado do nome, e mudar o nome da empresa a envia para análise de novo. O selo aparece ao lado do nome da sua empresa, inclusive nos convites.",
    },
    {
        "key": "languages",
        "question": "Quais idiomas são suportados?",
        "answer": "{count} idiomas, para o site, as entrevistas e os e-mails. Escolha o idioma em que uma entrevista é escrita, seja qual for o idioma da descrição da vaga.",
    },
    {
        "key": "privacy",
        "question": "O que acontece com as descrições de vaga e as respostas?",
        "answer": "As descrições de vaga são usadas para criar as entrevistas da sua empresa, e as respostas dos candidatos para avaliá-las para a sua empresa. As perguntas que a testee gera também podem ser reutilizadas em entrevistas e na prática de outras empresas, sem nada que identifique você, a sua empresa ou qualquer outra pessoa; você pode excluir disso as perguntas de uma entrevista nas configurações dela. A testee também extrai, da forma como as perguntas são respondidas, padrões gerais e anonimizados de qualidade das perguntas, para melhorar a forma como elas são geradas. A [política de privacidade](/privacy) explica o que guardamos, por quanto tempo e os direitos de cada pessoa.",
    },
    {
        "key": "eu_ai_law",
        "question": "É legal usar IA na triagem de candidatos na UE?",
        "answer": "Sim, com regras. Pelo Regulamento de IA da UE (AI Act), ferramentas que avaliam candidatos muito provavelmente são de alto risco, com obrigações a partir de 2 de dezembro de 2027, e o GDPR já se aplica: uma pessoa toma a decisão de contratação, os candidatos são informados de que a IA é usada e são mantidos registros. A testee funciona assim: a IA escreve as perguntas, pessoas da sua empresa revisam os resultados e decidem, e os candidatos são informados antes de começar. Isso não é aconselhamento jurídico; [O uso de IA no recrutamento é legal na UE?](/guides/is-ai-hiring-legal-in-the-eu) explica as regras e as datas.",
    },
    {
        "key": "uk_us",
        "question": "Podemos usar a testee para candidatos no Reino Unido e nos Estados Unidos?",
        "answer": "Sim. O acordo de tratamento de dados cobre a legislação do Reino Unido e dos Estados Unidos, e as instruções para empresas e os modelos de aviso aos candidatos (com versões para a cidade de Nova York, Illinois e Colorado) cobrem o que você deve informar aos candidatos. Para vagas na cidade de Nova York, use-a só depois de cumprir o que a Local Law 144 exige de você: uma auditoria de viés independente no ano anterior ao uso, a publicação do seu resumo e um aviso aos candidatos com 10 dias úteis de antecedência. A exportação para auditoria de viés do Registro de ações dá ao seu auditor a nota e o resultado de cada candidato que terminou, para cruzar com as respostas que seus candidatos declararam eles mesmos.",
    },
    {
        "key": "emails",
        "question": "Quais e-mails a testee envia, e como faço para pará-los?",
        "answer": 'E-mails de serviço, como convites, relatórios, problemas de pagamento e mudanças nos nossos termos, são sempre enviados. Os demais, como o resumo de atividades diário, os lembretes e as novidades do produto, você escolhe em Configurações, na seção E-mails, ou cancela pelo link "Cancelar inscrição" em cada e-mail. Os candidatos podem parar de receber os e-mails da sua empresa, ou os lembretes de uma entrevista, pelos links nos convites e lembretes.',
    },
    {
        "key": "delete",
        "question": "Posso excluir minha conta?",
        "answer": "Sim, nas Configurações. Sua conta e seus dados são excluídos, e antes você pode baixar uma cópia dos seus dados. As novidades da testee aparecem nas suas notificações, o sino no topo; as mais importantes também chegam por e-mail como novidade do produto, só enquanto essa configuração estiver ativada.",
    },
    {
        "key": "report",
        "question": "Como relato um problema?",
        "answer": "Escreva para nós pela [página de contato](/contact) e cole o ID do que se trata: “copiar id” fica abaixo do nome de uma empresa, entrevista ou candidato, e o da sua conta, no menu da conta e em Configurações. Com o ID, encontramos na hora.",
    },
]
