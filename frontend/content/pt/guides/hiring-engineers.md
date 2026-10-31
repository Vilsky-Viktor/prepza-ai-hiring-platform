---
title: "Como contratar engenheiros: um processo estruturado da descrição da vaga à proposta"
seoTitle: "Como contratar engenheiros: processo seletivo estruturado"
description: "Passo a passo para contratar engenheiros de software: perfil da vaga, triagem, teste de conhecimentos, código, design de sistemas, entrevistas e proposta."
updated: "2026-10-29"
---

# Como contratar engenheiros: um processo estruturado da descrição da vaga à proposta

Contratar engenheiros é caro de um jeito fácil de não perceber: a maior parte do custo é o tempo dos seus próprios engenheiros. Cada hora que eles passam entrevistando alguém que não conhece a stack é uma hora que não passam construindo. Um bom processo coloca primeiro as verificações baratas e amplas e reserva as caras e profundas para as poucas pessoas com mais chance de sucesso.

Este guia mostra esse processo passo a passo. Ele se apoia na pesquisa sobre seleção onde a pesquisa é clara, e avisa onde ela não é.

## O processo em resumo

| Etapa | O que verifica | Quem dedica tempo |
| --- | --- | --- |
| 1. Perfil da vaga e descrição da vaga | O que a vaga realmente exige | Gestor da vaga, um engenheiro sênior |
| 2. Triagem de currículos ou candidaturas | Só requisitos obrigatórios | Recrutador ou gestor da vaga |
| 3. Triagem de conhecimentos | O que o candidato sabe da sua stack | O candidato; você lê os resultados |
| 4. Desafio para casa ou live coding | Se ele sabe escrever código que funciona | Um ou dois engenheiros |
| 5. Design de sistemas (vagas sênior) | Como ele raciocina sobre sistemas maiores | Um engenheiro sênior |
| 6. Entrevista comportamental estruturada | Como ele trabalha com outras pessoas | Gestor da vaga, um par |
| 7. Checagem de referências | Confirmar o que você ouviu | Gestor da vaga |
| 8. Decisão e proposta | Uma decisão justa e documentada | A equipe de contratação |

## O que diz a pesquisa

Grandes revisões da pesquisa sobre seleção comparam os métodos pelo quanto os seus resultados se relacionam com o desempenho posterior no trabalho. A revisão importante mais recente, de Sackett, Zhang, Berry e Lievens (2022), revisou para baixo as estimativas anteriores e concluiu que os melhores preditores, em média, eram todos medidas específicas da função ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). As estimativas deles, numa escala em que 0 significa nenhuma relação e 1 uma relação perfeita:

| Método | Validade estimada |
| --- | --- |
| Entrevistas estruturadas | 0,42 |
| Testes de conhecimentos da função | 0,40 |
| Testes de amostra de trabalho | 0,33 |
| Entrevistas não estruturadas | 0,19 |
| Anos de experiência na função | 0,07 |

Daí saem três lições para a contratação de engenheiros:

- **A estrutura importa mais que o formato.** A mesma entrevista com perguntas definidas e um guia de pontuação previu muito melhor que uma conversa sem estrutura.
- **Anos de experiência dizem pouco sozinhos.** "Cinco anos de Java" é um sinal fraco comparado com o que a pessoa realmente sabe e consegue fazer.
- **Combine métodos.** Nenhum método prevê bem o bastante para ser usado sozinho.

São médias de muitas funções e estudos, não garantias para a sua vaga. Os autores também observam que testes de conhecimentos e amostras de trabalho são adequados para vagas em que se espera que os candidatos já tenham formação ou experiência. Isso vale para a maioria das contratações de engenharia, mas não para um programa de aprendizes.

## Passo 1: Escreva um perfil da vaga e uma descrição da vaga claros

Antes de publicar qualquer coisa, escreva o que a pessoa vai fazer nos primeiros seis meses e o que ela precisa saber no primeiro dia. Seja específico:

- **Precisa saber:** "Escreve e revisa consultas em PostgreSQL, incluindo joins e índices" pode ser testado. "Bons conhecimentos de banco de dados" não pode.
- **Vai aprender no trabalho:** as suas ferramentas internas, o seu domínio de negócio, as partes da stack que você vai ensinar.
- **Nível:** o que separa, na sua equipe, uma contratação pleno de uma sênior, como ser dono de um serviço de ponta a ponta ou liderar decisões de design.

Alinhe isso com todos os envolvidos na contratação. Depois, escreva a descrição da vaga a partir daí. Uma descrição da vaga que corresponde ao trabalho real atrai as pessoas certas e facilita a preparação de cada etapa seguinte, porque cada teste e cada entrevista podem ser ligados a ela.

Mantenha curta a lista de "desejáveis". Listas longas de requisitos afastam pessoas qualificadas que não marcam todos os itens.

## Passo 2: Faça a triagem de currículos só por requisitos obrigatórios

Use o currículo ou a candidatura para verificações de sim ou não: autorização de trabalho, localização ou fuso horário se a vaga exigir, um idioma necessário e qualquer requisito sem o qual a vaga realmente não funciona.

Não ranqueie as pessoas pelo currículo. Cargos, nomes de empregadores e anos de experiência são preditores fracos, e currículos são difíceis de comparar de forma justa: um currículo forte pode refletir tanto uma boa escrita quanto um bom trabalho. Trate o currículo como um filtro para o que não pode ser testado e passe todos que forem aprovados para a triagem de conhecimentos.

## Passo 3: Faça uma triagem de conhecimentos curta

Esta é a etapa que mais economiza o tempo dos seus engenheiros. Antes que alguém passe uma hora numa entrevista ao vivo, verifique o que cada candidato sabe da sua stack.

Uma boa triagem de conhecimentos é:

- **Específica da vaga:** testa as linguagens, frameworks, bancos de dados e práticas do seu perfil da vaga, e não curiosidades genéricas.
- **Curta:** poucos tópicos com cerca de 10 perguntas cada, para que bons candidatos com outras propostas ainda a concluam.
- **Igual para todos:** os mesmos tópicos, o mesmo número de perguntas e os mesmos limites de tempo.

É aqui que a testee se encaixa. Ela transforma a sua descrição da vaga numa entrevista de conhecimentos de múltipla escolha cronometrada. Você revisa os tópicos propostos antes de qualquer pergunta ser escrita, então o teste cobre a sua stack e nada mais. Para uma vaga de engenharia, isso pode incluir:

- **Perguntas de leitura de código:** um pequeno trecho de código com perguntas sobre o que ele imprime ou retorna, o que faz, por que falha ou qual mudança o corrige.
- **SQL:** uma tabela pequena e uma consulta, com a pergunta de quais linhas voltam.
- **Conhecimento de arquitetura e frameworks:** trade-offs, como um framework se comporta, o que dá errado sob carga.

Cada candidato recebe seu próprio conjunto aleatório de perguntas, com contagem regressiva em cada uma. Você vê uma ficha de avaliação com cada resposta e quanto tempo levou, além de alertas para respostas rápidas demais, saídas da página, tentativas de cópia e padrões incomuns nas respostas e nos tempos. Um alerta é um motivo para olhar com mais atenção, não prova de nada. O relatório também sugere perguntas que o candidato acertou, para explorar na próxima entrevista.

O que a testee não faz: os candidatos não escrevem, executam nem depuram código na testee. Ler código e escrever código são habilidades diferentes, então a próxima etapa continua importante. Veja os [testes de habilidades por cargo](/tests) para começar com testes prontos.

## Passo 4: Desafio para casa ou live coding

Agora verifique se os candidatos sabem escrever código que funciona. Esta é a etapa para escrever, executar e depurar código, seja com o seu próprio exercício, seja numa plataforma para desenvolvedores. Veja [Alternativas ao HackerRank](/compare/hackerrank-alternatives) para entender como uma triagem de conhecimentos e uma plataforma de programação se encaixam.

Dois formatos comuns:

- **Desafio para casa:** realista e com pouca pressão, mas ocupa as noites dos candidatos. Limite a poucas horas no máximo, diga quanto tempo deve levar e avalie com uma rubrica escrita.
- **Live coding:** mais curto e mais difícil de terceirizar, mas mais estressante. Faça pair programming num problema realista, deixe os candidatos usarem a linguagem que conhecem melhor e avalie o raciocínio, não só se terminaram.

Em qualquer caso, pontue com critérios combinados antes: correção, legibilidade, testes, como lidam com casos extremos. Como a triagem de conhecimentos já filtrou o grupo, você faz esta etapa com um punhado de pessoas, e não com todo mundo.

## Passo 5: Design de sistemas para vagas sênior

Para engenheiros sênior, acrescente uma conversa de design: "Como você construiria um serviço que faz X?" Observe como eles esclarecem requisitos, escolhem entre trade-offs e identificam pontos de falha. Raramente existe uma única resposta certa, então uma rubrica é essencial. Escreva como é uma resposta fraca, sólida e forte antes da primeira entrevista.

Pule esta etapa em vagas júnior, em que ela mede mais a autoconfiança do que a habilidade.

## Passo 6: Entrevistas comportamentais estruturadas com rubricas

As entrevistas estruturadas foram o melhor preditor isolado em Sackett et al. (2022). Estrutura significa:

- **As mesmas perguntas para todos os candidatos,** ligadas ao perfil da vaga: "Conte sobre uma vez em que você discordou de uma decisão de design. O que você fez?"
- **Uma rubrica de pontuação para cada pergunta,** com exemplos de respostas fracas, sólidas e fortes.
- **Notas independentes:** cada entrevistador dá a sua nota antes de discutir com os outros, para que a opinião mais barulhenta não defina o resultado.

Use esta etapa para o que os testes não mostram: colaboração, senso de dono, como a pessoa lida com feedback, como se comunica com quem não é engenheiro.

## Passo 7: Checagem de referências

Referências podem confirmar o que você descobriu e revelar preocupações, mas trate-as como uma checagem final, não como um teste decisivo. Sackett et al. não chegaram a uma estimativa de validade para checagem de referências porque a pesquisa disponível era escassa demais, então há pouca evidência sobre o quanto elas preveem o desempenho. Se você fizer, faça a todas as referências as mesmas poucas perguntas sobre comportamentos específicos.

## Passo 8: Experiência do candidato e tempo até a proposta

Bons engenheiros costumam participar de vários processos ao mesmo tempo. Um processo lento ou confuso faz você perdê-los.

- **Explique o processo inteiro logo no início:** as etapas, quanto tempo cada uma leva e quando eles terão retorno.
- **Seja breve.** Agende as últimas etapas próximas umas das outras e decida logo após a última entrevista.
- **Respeite o tempo deles.** Uma triagem de conhecimentos curta no começo significa que menos pessoas passam por entrevistas longas que dificilmente passariam.
- **Dê retorno no prazo para todos,** inclusive para quem não segue no processo.

## Imparcialidade em todo o processo

Um processo estruturado também é mais justo, mas só se você o aplicar de forma consistente:

- **Perguntas consistentes** em cada etapa, para todos os candidatos da mesma vaga.
- **Rubricas escritas com antecedência,** para que todos sejam avaliados pelos mesmos critérios.
- **Adaptações:** ofereça tempo extra ou outro formato aos candidatos que pedirem, por exemplo por causa de uma deficiência. Na testee, você pode dar tempo extra a um candidato antes de ele começar.
- **Acompanhe os resultados.** Métodos diferentes mostram diferenças de pontuação diferentes entre grupos. Sackett et al. encontraram diferenças médias maiores em testes de conhecimentos da função e amostras de trabalho do que em entrevistas estruturadas, o que é mais um motivo para combinar métodos. Acompanhe as taxas de aprovação em cada etapa.
- **Pessoas decidem.** Uma pontuação apoia uma decisão; ela não toma a decisão. Olhe as respostas antes de reprovar alguém.

Para o básico jurídico, incluindo o Regulamento de IA da UE (EU AI Act) e as regras americanas sobre taxas de seleção, veja [Testes de seleção](/pre-employment-testing).

## Resumo

Coloque primeiro as verificações amplas e baratas e por último as profundas e caras. Faça a triagem de currículos por requisitos obrigatórios, aplique uma triagem de conhecimentos curta e depois use o tempo dos engenheiros em programação, design e entrevistas estruturadas com os poucos que restarem. Pontue com rubricas escritas antes e mantenha o processo rápido e claro.

## Fontes

- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection: Addressing systematic overcorrection for restriction of range. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## Leitura relacionada

- [Testes de habilidades por cargo](/tests)
- [Alternativas ao HackerRank](/compare/hackerrank-alternatives)
- [Guia de testes de seleção](/pre-employment-testing)
- [Testes de habilidades x triagem de currículos](/guides/skills-tests-vs-cv-screening)
- [Entrevistando engenheiros na era da IA](/guides/interviewing-in-the-age-of-ai)
