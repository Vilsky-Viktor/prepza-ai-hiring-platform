---
title: "Agentes de IA, MCP e APIs: o que são e como usá-los no recrutamento"
seoTitle: "Agentes de IA, MCP e APIs no recrutamento: como usar"
description: "O que são agentes de IA, MCP e APIs, como usá-los com segurança no recrutamento e operar a prepza pela assistente de IA, Claude, ChatGPT ou sua plataforma."
updated: "2026-10-22"
---

# Agentes de IA, MCP e APIs: o que são e como usá-los no recrutamento

A maioria das pessoas conheceu a IA como uma janela de chat: você pergunta, ela responde. Um agente de IA vai um passo além. Ele consegue consultar informações nas suas ferramentas e, quando você pede, fazer coisas nelas: criar uma entrevista, convidar uma lista de candidatos, dizer quem teve a nota mais alta na semana passada. O Model Context Protocol (MCP) é o padrão que permite que o chat de IA que você já usa, como o Claude ou o ChatGPT, se conecte a ferramentas como essas. E uma API é a forma mais antiga e mais precisa de um software conversar com outro, sem IA no meio.

Este guia explica os três em termos simples, para que servem no recrutamento, com o que tomar cuidado e como usá-los com a prepza.

## O que é um agente de IA

Um chatbot só escreve texto. Um agente é um modelo de linguagem com **ferramentas**: ações pequenas e bem definidas que ele pode acionar, como "listar os candidatos desta entrevista" ou "convidar este e-mail". Quando você pergunta algo, o agente decide quais ferramentas usar, lê o que elas retornam e responde com base nisso, não de memória.

| Um chatbot | Um agente de IA |
| --- | --- |
| Responde com o que aprendeu no treinamento | Responde com os seus dados atualizados, lidos pelas ferramentas |
| Só consegue descrever como fazer algo | Consegue fazer, quando você pede e permite |
| Chuta quando não sabe | Consulta, ou diz que não consegue |
| Vive em uma única janela | Trabalha dentro das ferramentas às quais você o conecta |

São as ferramentas que tornam um agente útil, e também o que o torna seguro ou não. Um bom agente só pode usar as ferramentas que recebe, só com as suas permissões, e só faz o que você pediu.

## O que é o MCP

O Model Context Protocol é um padrão aberto, lançado pela Anthropic no fim de 2024 e hoje compatível com o Claude, o ChatGPT e muitos outros apps de IA e ferramentas para desenvolvedores. Ele costuma ser comparado a uma porta USB-C para a IA: em vez de cada app de IA criar a própria conexão com cada ferramenta, uma ferramenta oferece um único **servidor MCP**, e qualquer app de IA que fale MCP pode usá-lo.

Um servidor MCP informa três coisas ao app de IA:

1. **Quais ferramentas existem**, com um nome, uma descrição e os dados de que cada uma precisa.
2. **Quais ferramentas só leem** e quais alteram algo, para que o app de IA possa perguntar a você antes de uma alteração.
3. **Quem você é**, por meio de um login que você aprova uma única vez, para que cada chamada seja feita em seu nome, com as suas permissões.

Na prática, isso significa que você pode trabalhar com uma ferramenta a partir do chat que já usa, sem copiar dados de uma janela para outra.

## O que é uma API, e qual é a diferença

Uma API (interface de programação de aplicações) é um conjunto de requisições fixas que um programa pode enviar a outro: "listar os candidatos desta entrevista", "convidar este e-mail". Os seus desenvolvedores escrevem o código que as envia. Não há IA envolvida: a mesma requisição sempre faz a mesma coisa, que é exatamente o que você quer em uma automação que roda sozinha.

| | Mira, a assistente de IA (no app) | MCP (no Claude ou no ChatGPT) | API |
| --- | --- | --- | --- |
| Quem usa | Você, na prepza | Você, no seu chat de IA | O código da sua plataforma |
| Como pedir | Com as suas palavras | Com as suas palavras | Requisições fixas escritas por um desenvolvedor |
| Quem aprova as alterações | Você, em um card | Você, no seu app de IA | O seu código, como foi escrito |
| Ideal para | Perguntas e tarefas rápidas | Combinar a prepza com as suas outras ferramentas e arquivos | Automações que rodam sem ninguém acompanhando |
| Entra como | Você | Você | Uma chave da empresa |

Use a Mira ou o MCP quando houver uma pessoa acompanhando. Use a API quando o seu próprio sistema precisar convidar candidatos e coletar os resultados sozinho, por exemplo a partir de um site de carreiras ou de uma ferramenta interna de RH.

## Para que isso serve no recrutamento

O recrutamento tem muitas etapas pequenas e repetitivas espalhadas por várias ferramentas. Um agente é bom exatamente nisso:

- **Perguntas sobre o seu funil.** "Quais candidatos para Senior Backend foram aprovados esta semana?", "Quem ainda não começou a entrevista?", "Qual é a nossa nota média para a vaga de analista de dados?"
- **Configurações.** "Crie uma entrevista a partir desta descrição da vaga", "Defina a nota de aprovação em 70%", "Dê a este candidato 50% de tempo extra."
- **Tarefas em massa.** "Convide estas 12 pessoas para a entrevista de frontend", colado direto de um e-mail ou de uma planilha.
- **Combinar fontes.** No Claude ou no ChatGPT, você pode usar a prepza junto com as suas outras ferramentas e arquivos conectados: comparar uma descrição de vaga dos seus documentos com os tópicos da entrevista, ou rascunhar uma mensagem para os candidatos pré-selecionados.

O que ele não deve fazer é tomar a decisão de contratação. Uma nota apoia o julgamento de uma pessoa; não o substitui. Peça ao agente para ordenar, resumir e preparar, e deixe a decisão com uma pessoa. Veja [O uso de IA no recrutamento é legal na UE?](/guides/is-ai-hiring-legal-in-the-eu) para entender por que isso também importa do ponto de vista legal.

## Com o que tomar cuidado

Conectar uma IA aos seus dados de recrutamento merece o mesmo cuidado que dar acesso a um colega.

| Risco | O que ajuda |
| --- | --- |
| O agente faz algo que você não queria | As alterações precisam da sua aprovação antes, e ele só faz o que você pediu |
| Ele vê mais do que deveria | Ele age como você: vê o que você vê, nada mais |
| Instruções escondidas nos dados | Nomes, respostas e documentos dos candidatos são dados, nunca instruções a seguir |
| Segredos que vão parar em um chat | Chaves de API e senhas nunca passam pelo chat |
| Erros irreversíveis | Excluir uma conta ou uma empresa continua no app, com a sua própria confirmação |
| Dados que saem das suas ferramentas | Os dados chegam ao app de IA que você conecta, sob os termos desse app: conecte só apps que a sua empresa permite |
| Uso descontrolado | Limites de quantas ações são executadas por hora |

Antes de conectar qualquer app de IA a dados de trabalho, confira a política da sua empresa sobre ferramentas de IA e informe os candidatos, no seu aviso de privacidade, sobre quais serviços tratam os dados deles.

## Três formas de trabalhar com a prepza além das páginas dela

### 1. Mira, a assistente de IA integrada

Selecione **perguntar à Mira** no cabeçalho de qualquer página. A Mira, assistente de IA da prepza, conhece as suas empresas, entrevistas, candidatos, créditos e integrações, e sabe como a prepza funciona. Ela responde no seu idioma, e você pode digitar ou falar.

- **Ele responde com os seus dados**, com a mesma visão que você tem: um administrador vê o que um administrador vê, um visualizador o que um visualizador vê.
- **Ele sabe em que página você está.** Pergunte "O que posso fazer nesta página?" para ver o guia dessa página, ou "Quem é o melhor aqui?" nos candidatos de uma entrevista, e ele responde sobre essa entrevista sem perguntar qual.
- **Ele prepara as alterações, você as confirma.** Se você pedir para convidar candidatos, ele mostra um card com exatamente o que vai acontecer, como "Convidar 12 candidatos para Backend developer". Nada é executado até você selecionar Confirmar.
- **Ele mostra as fontes.** Abaixo de uma resposta aparecem os candidatos ou as entrevistas que ele usou e um link para a página de onde vieram.
- **Ele não foge do assunto.** Responde sobre a prepza e sobre recrutar com ela, e recusa o resto.

### 2. A prepza no Claude ou no ChatGPT, via MCP

Se a sua equipe já trabalha no Claude ou no ChatGPT, você pode levar a prepza para lá. O servidor MCP da prepza oferece as mesmas ferramentas que a Mira, a assistente integrada.

**Para conectar:**

1. Na prepza, abra a aba **Integrações** de uma empresa e selecione **Apps de IA**. Copie o endereço do servidor: `https://prepza.ai/mcp`.
2. **No Claude:** abra Configurações, depois Conectores, e adicione um conector personalizado com esse endereço. **No Claude Code:** execute `claude mcp add --transport http prepza https://prepza.ai/mcp`. **No ChatGPT:** adicione-o como conector personalizado nas configurações de apps e conectores.
3. O seu app de IA abre o login da prepza. Faça login, confira qual app está pedindo acesso e selecione **Permitir**. Para que ele possa apenas ler, desative antes **Permitir alterações**.

A partir daí, pergunte no seu chat como perguntaria a um colega: "Na prepza, quem são os três melhores candidatos para Product designer?" A maioria dos apps de IA pergunta a você antes de uma alteração e avisa antes de qualquer ação que não possa ser desfeita: a prepza informa a eles quais ações alteram ou excluem algo.

**O que continua igual ao app:**

- **As suas permissões.** Ele age como você, em cada empresa de que você faz parte, com o seu papel em cada uma.
- **Créditos e limites.** Convidar um candidato custa o mesmo que no app, e os mesmos limites de e-mail se aplicam.
- **O registro.** Tudo o que um app de IA faz por você aparece no registro de ações da empresa como feito por meio de um app de IA, de aprovar tópicos e ver resultados a dar tempo extra ou revogar um candidato. O proprietário da empresa o lê na aba **Registro de ações** da empresa.
- **A empresa decide.** Proprietários e administradores podem impedir que apps de IA usem os dados de uma empresa com **Permitir apps de IA nesta empresa** na página de apps de IA dela.
- **O que ele não pode fazer.** Ele não vê a sua senha nem as suas chaves de API, e não pode excluir a sua conta nem uma empresa. Isso continua no app.

**Para desconectar,** remova o conector no seu app de IA ou selecione **Desconectar** ao lado dele em **Apps de IA**, na aba Integrações. Ele para de funcionar na hora.

**Outros apps e seus próprios agentes.** A [aba MCP](/api-docs?tab=mcp) da documentação para desenvolvedores traz os passos para Gemini CLI, Cursor, VS Code e Le Chat, e agentes de exemplo completos em Python e TypeScript. Um agente que roda em um servidor, sem ninguém para aprovar um login, usa uma chave de API da empresa com a permissão **Usar com agentes de IA (MCP)**: ele funciona só nessa empresa, e só com as ferramentas que as outras permissões da chave permitem.

### 3. A sua própria plataforma, via API

Para automações sem IA, a prepza tem uma API, descrita na [documentação para desenvolvedores](/api-docs).

1. Um proprietário ou administrador abre a aba **Integrações** de uma empresa, depois **API**, e seleciona **Nova chave**. Dê a ela o nome da plataforma que vai usá-la, escolha quando ela expira e marque só o que ela precisa: a chave de um painel só lê; a de um site de carreiras também convida. Depois você pode adicionar ou tirar permissões. A chave aparece só uma vez; guarde-a em um lugar seguro.
2. A sua plataforma envia requisições com essa chave: listar as entrevistas da empresa, listar ou consultar candidatos com a nota, se foram aprovados e os alertas de integridade, e convidar um candidato.
3. Adicione um **webhook**: um endereço na sua plataforma que a prepza chama, com assinatura, quando um candidato começa ou termina, quando o convite não chega até ele ou expira, quando ele é removido e quando uma entrevista fica pronta, para que você não precise ficar perguntando. A página da API pode enviar a ele um evento de teste e mostra o registro de entregas dele.

Cada candidato vem com um link para os resultados completos na prepza e, até terminar, com o próprio link de convite, para que a sua plataforma possa enviá-lo em uma mensagem própria, se você preferir. Quando a sua plataforma já sabe quem é o candidato, convide-o sem login: a prepza não envia e-mails, e o candidato faz a entrevista pelo link sem entrar na prepza, então envie o link só para ele. Um convite também pode levar o candidato de volta ao seu site (qualquer endereço https) com um botão na página final e definir um tema claro ou escuro nas cores da sua empresa. Com o SDK da prepza, a sua própria página pode exibir a entrevista em si, mas só nos sites que a sua empresa permite na página da API. A API e os webhooks não dependem desses sites: em vez disso, cada chave pode ser limitada aos endereços IP dos seus servidores. A verificação só adiciona o selo de empresa verificada.

Vale a mesma regra de sempre: a nota apoia a decisão de uma pessoa, então não reprove candidatos automaticamente com base nela.

## Qual usar e quando

Comece por quem faz o trabalho e com que frequência.

| A sua situação | O que usar |
| --- | --- |
| Você está na prepza e quer uma resposta rápida: quem foi aprovado, quem não começou, quantos créditos restam | Mira, a assistente integrada |
| Você quer configurar algo em poucas palavras: uma entrevista a partir de uma descrição da vaga, uma nota de aprovação, tempo extra | Mira, a assistente integrada |
| Você já trabalha no Claude ou no ChatGPT o dia todo e quer a prepza lá também | MCP |
| A tarefa precisa da prepza e de outra coisa: os seus documentos, rascunhos de e-mail, outra ferramenta conectada | MCP |
| Um recrutador fora do escritório quer acompanhar o funil pelo app de IA no celular | MCP |
| O seu site de carreiras ou sistema de RH deve convidar candidatos sozinho, sem ninguém clicar | A API |
| Os resultados devem chegar ao seu próprio banco de dados ou painel assim que os candidatos terminam | A API, com um webhook |
| O seu ATS é um dos que a prepza integra (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Nenhum deles: conecte o ATS na aba Integrações. Veja [Como integrar testes de habilidades ao seu ATS](/guides/ats-integration-skills-tests) |

Uma regra prática:

- **Uma pessoa pede e confere cada alteração:** a Mira na prepza, ou o MCP se essa pessoa vive no Claude ou no ChatGPT.
- **Um software age sozinho, sempre do mesmo jeito:** a API.
- **Para começar:** experimente primeiro a Mira, a assistente integrada. Ela não precisa de configuração, e o que você aprender vale também para o MCP.

Eles também funcionam juntos. Uma equipe pode enviar convites pelo sistema de RH via API, enquanto os recrutadores perguntam sobre os resultados à Mira ou ao seu chat de IA.

## Como ter bons resultados

- **Dê nome às coisas.** "A entrevista Senior Backend" funciona melhor que "aquela entrevista".
- **Peça uma etapa de cada vez** quando importa. Confira o resultado e depois peça a próxima.
- **Leia a aprovação antes de permitir.** Ela mostra exatamente o que vai ser executado.
- **Pergunte de onde veio um número.** Um bom agente consegue apontar os candidatos ou a página por trás dele.
- **Deixe as decisões com as pessoas.** Use o agente para encontrar, ordenar e preparar; a decisão é sua.

## Preços

A Mira, a conexão MCP e a API são gratuitas. Você paga só pelos candidatos, como sempre: por candidato que responde pelo menos uma pergunta, sem assinatura. Veja os [preços](/pricing).

## Leitura relacionada

- [Como integrar testes de habilidades ao seu ATS](/guides/ats-integration-skills-tests)
- [Entrevistando engenheiros na era da IA](/guides/interviewing-in-the-age-of-ai)
- [O uso de IA no recrutamento é legal na UE?](/guides/is-ai-hiring-legal-in-the-eu)
