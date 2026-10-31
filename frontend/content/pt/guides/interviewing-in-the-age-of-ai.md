---
title: "Entrevistando engenheiros na era da IA: o que avaliar agora"
seoTitle: "Entrevista técnica na era da IA: o que avaliar agora"
description: "Assistentes de IA já fazem parte do dia a dia da engenharia. Como isso muda o que as entrevistas devem avaliar e onde entram os testes de conhecimentos."
updated: "2026-10-29"
---

# Entrevistando engenheiros na era da IA: o que avaliar agora

Durante anos, a entrevista técnica clássica pedia ao candidato que escrevesse código do zero: inverter uma lista, implementar um cache, resolver um quebra-cabeça num quadro branco ou num editor compartilhado. A ideia era simples. Se alguém sabe escrever o código, provavelmente sabe fazer o trabalho.

Os assistentes de programação com IA enfraqueceram essa ligação. Muitos trechos de código rotineiros agora podem ser rascunhados por um assistente em segundos, tanto no trabalho quanto, se você não impedir, durante uma entrevista remota. Isso não torna a habilidade de engenharia menos importante. Muda quais habilidades importam mais e, portanto, muda o que uma entrevista deve verificar.

Este guia mostra o que mudou, como algumas empresas estão se adaptando e como montar um processo de entrevistas que continue dizendo quem sabe fazer o trabalho. Ele foi escrito para gestores contratantes e líderes de engenharia.

## O que mudou

Os assistentes de IA já fazem parte do trabalho diário de muitos desenvolvedores. Na Stack Overflow Developer Survey de 2025, 84% dos respondentes disseram que usam ou planejam usar ferramentas de IA no processo de desenvolvimento, e 51% dos desenvolvedores profissionais disseram que as usam diariamente ([Stack Overflow, 2025](https://survey.stackoverflow.co/2025/ai)). O relatório Octoverse 2025 do GitHub diz que 80% dos novos desenvolvedores no GitHub usam o Copilot na primeira semana ([GitHub, outubro de 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)).

A mesma pesquisa mostra os limites. Mais respondentes desconfiavam da precisão das respostas da IA (cerca de 46%) do que confiavam nela (cerca de 33%). A frustração mais comum, citada por 66%, eram "soluções de IA que estão quase certas, mas não totalmente", e 45% disseram que depurar código gerado por IA leva mais tempo ([Stack Overflow, 2025](https://survey.stackoverflow.co/2025/ai)).

Juntos, esses números descrevem uma mudança no próprio trabalho. Produzir um primeiro rascunho de código está ficando mais barato. Julgar se esse rascunho está certo, e corrigi-lo quando não está, é onde agora está boa parte da habilidade.

## Como as empresas estão se adaptando

Ainda não existe uma resposta única no setor. As abordagens divulgadas vão em direções diferentes:

- **Permitir ou exigir IA na entrevista.** Em junho de 2025, a Canva disse que agora espera que candidatos de backend, machine learning e frontend usem ferramentas de IA como Copilot, Cursor e Claude numa nova etapa de "programação assistida por IA". Ela avalia se os candidatos conseguem "decompor requisitos complexos e ambíguos", "identificar e corrigir problemas em código gerado por IA" e "garantir que as soluções geradas por IA atendam aos padrões de produção" ([Canva Engineering, junho de 2025](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews)).
- **Testar etapas de programação assistida por IA.** Em julho de 2025, o Business Today, citando o 404 Media, noticiou que a Meta estava criando uma entrevista de programação em que os candidatos têm um assistente de IA. O texto citava a Meta dizendo que isso é "mais representativo do ambiente de desenvolvimento em que nossos futuros funcionários vão trabalhar, e também torna a cola baseada em LLM menos eficaz" ([Business Today, julho de 2025](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31)).
- **Restringir ferramentas e voltar ao presencial.** Em março de 2025, a CNBC noticiou uma ferramenta criada para ajudar candidatos a usar IA sem serem notados em entrevistas remotas de programação. Na mesma reportagem, a Amazon disse que os candidatos precisam declarar que não vão usar ferramentas não autorizadas, o CEO do Google sugeriu que gestores contratantes considerem algumas entrevistas presenciais, e a Deloitte tinha voltado a fazer entrevistas presenciais no seu programa de trainees no Reino Unido ([CNBC via NBC New York, março de 2025](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1)).

São algumas poucas grandes empresas, não uma pesquisa de mercado, e as políticas mudam. Mas elas apontam na mesma direção: uma tarefa remota de "escreva isto do zero" agora é menos confiável, e a pergunta interessante passou de "você sabe produzir código?" para "você entende o código bem o bastante para julgá-lo?".

## Por que o conhecimento importa mais como primeiro filtro

Se um assistente pode rascunhar o código, o que separa um engenheiro forte de um fraco? Principalmente as coisas que um assistente não consegue fornecer no lugar dele:

- **Conceitos e teoria.** Saber como um banco de dados usa um índice, por que acontece uma condição de corrida ou o que um framework faz a cada requisição permite que um engenheiro perceba quando o código gerado está errado.
- **Leitura de código.** Antes de usar o que a IA produziu, alguém precisa ler e saber o que aquilo vai imprimir, retornar ou alterar.
- **Depuração.** Quando um código "quase certo" falha, a correção vem de entender o porquê.
- **Julgamento.** Escolher entre duas abordagens que funcionam exige conhecer os trade-offs: desempenho, segurança, manutenibilidade.

Essas são habilidades de conhecimento e raciocínio, e podem ser testadas de forma direta e rápida. A pesquisa sobre seleção já coloca os testes de conhecimentos da função entre os melhores preditores de desempenho no trabalho, em média: numa nova análise de 2022 de décadas de estudos, Sackett, Zhang, Berry e Lievens estimaram uma validade de 0,40 para testes de conhecimentos da função, perto das entrevistas estruturadas, com 0,42 ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). Essa pesquisa é anterior aos assistentes de IA, então não prova nada sobre o trabalho na era da IA. Mas ela apoia o uso de um teste de conhecimentos específico da função como primeiro filtro, e a mudança descrita acima torna o conhecimento que ele testa mais central para o trabalho, não menos.

## Os exercícios práticos continuam tendo seu lugar

Nada disso torna os exercícios de programação inúteis. Muda quando você os aplica e como eles são:

- **Pair programming com IA.** Como na etapa da Canva, dê aos candidatos um assistente e uma tarefa realista e aberta. Observe como eles a decompõem, o que pedem ao assistente e o que aceitam ou rejeitam.
- **Code review.** Entregue um pull request, talvez escrito por IA, com alguns bugs reais. Pergunte o que eles mudariam e por quê.
- **Depuração.** Entregue uma pequena base de código com um teste falhando. Isso é próximo do trabalho diário que a pesquisa descreve e difícil de fingir.
- **Design de sistemas.** Para vagas sênior, uma conversa sobre trade-offs mostra um julgamento que nenhum prompt sozinho produz.

Esses exercícios exigem tempo de um engenheiro para aplicar e pontuar. Esse é o principal motivo para colocar antes deles uma verificação de conhecimentos rápida e ampla, para que cheguem a eles os candidatos com mais chance de sucesso.

## Um processo para a era da IA

1. **Faça a triagem das candidaturas só por requisitos obrigatórios:** autorização de trabalho, localização, experiência indispensável.
2. **Aplique uma triagem de conhecimentos curta** sobre conceitos, teoria e leitura de código da sua stack.
3. **Aplique um exercício prático** num formato que combine com o jeito de trabalhar da sua equipe: pair programming com IA, code review ou depuração, remoto ou presencial.
4. **Acrescente design de sistemas** para as vagas sênior.
5. **Faça uma entrevista estruturada** com perguntas definidas e uma rubrica de pontuação, incluindo como o candidato usa ferramentas de IA e verifica o que elas produzem.
6. **Deixe as pessoas decidirem,** com cada resultado como um dos elementos.

Diga aos candidatos logo no início quais ferramentas são permitidas em cada etapa. Uma regra clara é mais justa do que um jogo de adivinhação, e deixa os resultados mais fáceis de comparar.

Para a versão completa passo a passo, veja [Como contratar engenheiros](/guides/hiring-engineers).

## Onde a testee se encaixa

A testee é bem adequada para o passo 2. Ela transforma a sua descrição da vaga numa entrevista de conhecimentos de múltipla escolha cronometrada, e você revisa os tópicos propostos antes de qualquer pergunta ser escrita, então o teste cobre a sua stack e nada mais.

- **Conceitos e teoria a partir da descrição da vaga:** bancos de dados, APIs, arquitetura, o comportamento de um framework, práticas de segurança.
- **Perguntas de leitura de código:** um pequeno trecho de código com perguntas sobre o que ele imprime ou retorna, o que faz, por que falha ou qual mudança o corrige. É a mesma habilidade de revisão de que depende o trabalho assistido por IA.
- **Um cronômetro em cada pergunta:** cada pergunta tem sua própria contagem regressiva, controlada pelo servidor, e cada candidato recebe seu próprio conjunto aleatório de perguntas. Isso dificulta pesquisar as respostas, inclusive perguntando a um assistente de IA. Não torna impossível.
- **Sinais de integridade:** as fichas de avaliação sinalizam respostas rápidas demais para a pergunta ter sido lida, as vezes em que o candidato saiu da página e as tentativas de cópia. Quando o candidato termina, o relatório também aponta padrões de resposta que costumam aparecer quando alguém repassa as perguntas a uma IA e copia as respostas dela: mais ou menos o mesmo tempo em cada pergunta, independentemente da extensão ou da dificuldade, ou perguntas difíceis certas enquanto as fáceis estavam erradas. Um alerta ou padrão é um motivo para olhar com mais atenção, não prova de cola.
- **Perguntas para a entrevista ao vivo:** o relatório sugere até 3 perguntas que o candidato acertou, dos seus temas mais fortes, para discutir em uma entrevista ao vivo, onde nenhuma IA pode responder por ele.

O que a testee não faz: os candidatos não escrevem, executam nem depuram código na testee, e ela não observa como eles usam um assistente de IA. Isso fica para a etapa prática, feita internamente ou numa plataforma para desenvolvedores, que complementa a triagem de conhecimentos. Veja os [testes de habilidades por cargo](/tests) para começar com testes prontos, e [Entrevistas com IA](/ai-interviews) para ver como a testee usa a IA e o que deixa para as pessoas.

## Imparcialidade e experiência do candidato

Mudar o seu processo é um bom momento para verificar se ele é justo:

- **Deixe claras as regras sobre IA** em cada etapa, por escrito.
- **Mantenha as mesmas condições** para todos numa mesma etapa.
- **Ofereça adaptações,** como tempo extra, aos candidatos que pedirem.
- **Não trate um sinal como veredito.** Fazer uma pausa, desviar o olhar ou responder rápido pode ter causas inocentes.
- **Seja breve.** Cada etapa que você acrescenta custa aos bons candidatos um tempo que eles podem usar em outra proposta.

## Resumo

Os assistentes de IA baratearam a produção de código e tornaram mais importante saber julgá-lo. Um bom processo reflete isso: avalie conhecimento, teoria e leitura de código no início, onde é rápido e, com um cronômetro em cada pergunta, mais difícil de terceirizar, e depois use exercícios práticos, muitas vezes com IA permitida, para ver como os candidatos trabalham. Deixe as regras claras e mantenha as pessoas no comando da decisão.

## Fontes

- Stack Overflow, [2025 Developer Survey: AI](https://survey.stackoverflow.co/2025/ai).
- GitHub, [Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/), 28 de outubro de 2025.
- Canva Engineering, [Yes, you can use AI in our interviews](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews), 11 de junho de 2025.
- Business Today, [Meta to test job applicants with AI-assisted coding interviews](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31), 31 de julho de 2025, citando o 404 Media.
- CNBC via NBC New York, [Meet the 21-year-old helping coders use AI to cheat in Google and other tech job interviews](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1), 9 de março de 2025.
- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## Leitura relacionada

- [Como contratar engenheiros](/guides/hiring-engineers)
- [Testes de habilidades por cargo](/tests)
- [Cola em testes de recrutamento online, e o que funciona contra ela](/guides/cheating-in-online-assessments)
- [Entrevistas com IA: o que são e como usá-las de forma justa](/ai-interviews)
- [Testes de habilidades x triagem de currículos](/guides/skills-tests-vs-cv-screening)
