---
title: "Como integrar testes de habilidades ao seu ATS"
seoTitle: "Como integrar testes de habilidades ao ATS: guia prático"
description: "Envie testes de habilidades e receba os resultados pelo ATS automaticamente, deixe as decisões de contratação com pessoas e saiba o que checar primeiro."
updated: "2026-10-21"
---

# Como integrar testes de habilidades ao seu ATS

A maioria das equipes de recrutamento gerencia os candidatos em um sistema de rastreamento de candidatos (ATS) e aplica testes de habilidades em outra ferramenta. Sem uma conexão entre os dois, alguém copia e-mails do ATS, envia convites manualmente, espera e depois copia as notas de volta. Com cinco candidatos, funciona. Com cinquenta, os convites saem atrasados, os resultados ficam em uma segunda aba que ninguém abre, e bons candidatos aceitam outras propostas enquanto esperam.

Este guia explica o que faz uma boa conexão entre um ATS e uma ferramenta de testes, o que verificar antes de depender dela e como configurá-la para que a automação cuide do trabalho repetitivo enquanto as pessoas continuam tomando todas as decisões de contratação.

## Por que integrar

| Sem integração | Com integração |
| --- | --- |
| Alguém exporta ou copia os e-mails dos candidatos | Mover um candidato para uma etapa envia o convite |
| Os convites saem quando alguém tem tempo | Os convites saem minutos depois da mudança de etapa |
| Os resultados ficam na ferramenta de testes | Os resultados aparecem no candidato dentro do ATS |
| Gestores perguntam: "Alguém já testou essas pessoas?" | O ATS mostra quem fez o teste e como se saiu |
| Erros de digitação nos e-mails e candidatos esquecidos | O ATS é a lista única de quem se candidatou |

A velocidade importa mais do que parece. Quanto maior o intervalo entre a candidatura e o retorno, mais candidatos desistem ou aceitam outro emprego. As taxas exatas de desistência variam muito conforme a vaga e o mercado, então trate os números publicados com cautela, mas a tendência é consistente: um processo lento perde pessoas, e os melhores candidatos costumam ter mais opções.

## Como é um bom fluxo

Uma boa integração segue as etapas que você já usa. Ela não inventa um processo novo.

1. **Um candidato se inscreve** e entra no seu ATS como sempre.
2. **Uma pessoa move o candidato para uma etapa de teste,** por exemplo "Teste de habilidades". Essa mudança é o gatilho, então uma pessoa continua decidindo quem faz o teste.
3. **A ferramenta de testes envia o convite** automaticamente, para o teste vinculado àquela vaga.
4. **O candidato faz o teste** quando puder, dentro do prazo que você definir.
5. **Os resultados são registrados no candidato dentro do ATS:** a nota, se foi aprovado, eventuais alertas de integridade e um link para as respostas completas.
6. **Uma pessoa analisa o resultado** e avança com o candidato, ou não.

Duas coisas continuam manuais de propósito: escolher quem faz o teste e decidir o que acontece depois. A integração só elimina a cópia entre uma coisa e outra.

### Por que não disparar o teste a cada nova candidatura?

Algumas ferramentas convidam todo mundo que se candidata. Isso pode funcionar em vagas de alto volume, em que todos fazem o mesmo teste. Mas uma etapa para a qual você move os candidatos é mais fácil de controlar: você pode pular quem claramente não atende a um requisito obrigatório (sem autorização de trabalho, localização errada) e nunca testa, nem paga por, alguém que você já ia reprovar de qualquer forma.

## O que verificar antes de escolher uma integração

Nem toda promessa de "integra com o seu ATS" significa a mesma coisa. Faça estas perguntas antes de conectar qualquer coisa.

| Pergunta | Por que importa | Uma boa resposta |
| --- | --- | --- |
| Como é feita a conexão? | Senhas compartilhadas e contas mantidas pelo fornecedor são difíceis de auditar ou revogar | Uma chave de API ou token que a sua empresa cria e pode excluir a qualquer momento |
| O que a chave pode fazer? | Uma chave com acesso total é um risco se vazar | As permissões mínimas de que a integração precisa, listadas na documentação |
| O que dispara um convite? | Você precisa saber exatamente quando os candidatos recebem e-mails | Uma etapa específica que você escolhe para cada vaga |
| Onde os resultados aparecem? | Resultados que ninguém vê não ajudam | No perfil do candidato, como nota ou comentário que a sua equipe já lê |
| O que acontece quando um convite falha? | Sem créditos, um erro de digitação, uma conta pausada: candidatos ficam travados sem ninguém saber | Alguém é avisado, e o candidato pode ser convidado de novo |
| Um evento pode ser processado duas vezes? | ATSs reenviam eventos; um candidato não deveria receber dois convites | Cada candidato é convidado uma vez por teste, não importa quantas vezes o evento chegue |
| Como os eventos recebidos são verificados? | Um endereço sem verificação pode receber eventos falsos | Requisições assinadas que a ferramenta confere |
| Por quanto tempo os dados dos candidatos são guardados? | Leis de privacidade como o GDPR exigem um prazo de retenção claro | Um prazo informado, e exclusão quando você exclui a vaga, o teste ou a sua conta |
| Quanto custa? | Planos por usuário podem deixar a automação cara | Um custo previsível por candidato testado |

Se o fornecedor não consegue responder com clareza às perguntas sobre falhas e duplicidades, espere descobrir a resposta da pior forma.

### Proteção de dados

Conectar dois sistemas significa que dados de candidatos, no mínimo nomes e e-mails, circulam entre duas empresas. Pelo GDPR e leis semelhantes, o seu fornecedor de testes geralmente atua como operador dos dados, então você precisa de um contrato de tratamento de dados e deve informar aos candidatos, no aviso de privacidade ou no convite, que um teste de habilidades faz parte do processo. Repasse apenas os dados de que o teste realmente precisa. Para saber mais sobre o lado jurídico dos testes e da IA no recrutamento, veja [O uso de IA no recrutamento é legal na UE?](/guides/is-ai-hiring-legal-in-the-eu)

## Checklist de configuração

Antes de ativar a integração em uma vaga real:

1. **Crie uma etapa só para testes** no seu ATS, como "Teste de habilidades". Não reaproveite uma etapa que significa outra coisa, ou candidatos serão convidados por engano.
2. **Crie a chave a partir de uma conta de administrador** que veja todas as vagas que você quer vincular, apenas com as permissões listadas na documentação.
3. **Vincule cada vaga ao seu teste** e escolha a etapa que dispara o convite.
4. **Configure o webhook** se o seu ATS exigir que isso seja feito manualmente, e cole o segredo dele onde a ferramenta pedir.
5. **Teste com você mesmo.** Adicione um candidato com o seu próprio e-mail, mova-o para a etapa, faça o teste e confira se a nota aparece no ATS.
6. **Defina quem acompanha as falhas:** quem é avisado quando um convite não pode ser enviado e quem resolve.
7. **Combine como os resultados serão lidos.** Uma nota de aprovação é uma referência, não uma reprovação automática. Decida isso antes de os resultados chegarem, não depois.

## Erros comuns

- **Automatizar a decisão, e não a burocracia.** Reprovar automaticamente todos abaixo de uma nota elimina a revisão humana que identifica uma pergunta ruim ou um candidato que teve problema de conexão. Deixe a nota ordenar; deixe uma pessoa decidir.
- **Disparar a partir da etapa errada.** Uma etapa que os recrutadores usam por outros motivos envia testes para pessoas que não deveriam recebê-los.
- **Um teste para todas as vagas.** A integração facilita enviar o mesmo teste para todo lugar. Um teste ajuda mais quando é feito para a vaga em questão. Veja [Testes de habilidades x triagem de currículos](/guides/skills-tests-vs-cv-screening).
- **Ninguém acompanhando as falhas.** Se um convite falha sem aviso, o candidato espera um e-mail que nunca chega, e você acha que ele ignorou.
- **Uma chave ligada a alguém que vai sair.** Algumas chaves de ATS agem em nome de quem as criou. Quando a conta dessa pessoa é encerrada, a integração para. Use uma conta que vai permanecer e reconecte quando as pessoas mudarem de função.
- **Esquecer os candidatos fora do ATS.** Indicações e candidatos diretos que nunca entram no ATS também precisam de convite. Mantenha também uma forma manual de convidá-los.

## Como a testee faz

A testee se integra com **Workable, Greenhouse, Teamtailor, Recruitee e Breezy HR**. Ela segue o fluxo descrito acima.

- **Sua chave, seu controle.** Um proprietário ou administrador conecta o ATS na aba Integrações da empresa com uma chave que a sua empresa cria no ATS. A testee verifica a chave antes de salvar, guarda-a criptografada e nunca mais a mostra. Desconectar exclui a chave e as vagas vinculadas na hora.
- **Vincule uma vaga a uma entrevista.** Escolha uma vaga do ATS e a etapa que dispara o convite, e vincule-a a uma entrevista existente na testee ou crie uma nova a partir do texto da vaga no ATS. Você revisa os temas antes de qualquer pergunta ser escrita.
- **Mova o candidato, e o convite sai.** Cada candidato é convidado uma vez por entrevista, mesmo que o ATS envie o mesmo evento duas vezes.
- **Resultados de volta no ATS.** Quando um candidato termina, a testee adiciona uma nota ou comentário a ele no ATS com a nota obtida, se foi aprovado, eventuais alertas de integridade (sair da página, tentativas de copiar, respostas escolhidas rápido demais para ter lido a pergunta) e um link para a ficha de avaliação com todas as respostas.
- **Falhas não passam despercebidas.** Se um candidato não puder ser convidado, por exemplo porque a empresa ficou sem créditos, atingiu um limite de e-mails, ou porque a testee pausou os convites temporariamente, todos os membros da empresa recebem uma notificação com o nome do ATS. Candidatos não convidados por falta de créditos são convidados automaticamente após uma recarga, e os candidatos em espera de qualquer vaga podem ser convidados de novo com um clique.
- **Slack, se você usa.** A testee pode publicar notificações, como um candidato que terminou ou um candidato do ATS que não pôde ser convidado, em um canal do Slack que você escolher.
- **Sua própria plataforma.** Se o seu ATS não está na lista, a [API](/api-docs) da testee permite convidar candidatos com uma chave de API e receber um webhook assinado quando um candidato começa ou termina, quando o convite não chega até ele ou expira, quando ele é removido e quando uma entrevista fica pronta.
- **Dados guardados por um prazo definido.** Candidatos salvos a partir de um ATS são excluídos após 365 dias, ou antes, junto com a entrevista ou a empresa.

Alguns ATSs exigem uma etapa do lado deles. Greenhouse, Teamtailor e Recruitee pedem que você adicione um webhook manualmente; a janela Instruções da testee mostra o endereço e onde colar o segredo. A testee configura sozinha os webhooks do Workable e do Breezy HR.

O preço é por candidato, sem assinatura: você paga só pelos candidatos que respondem pelo menos uma pergunta, $5 cada na recarga de $50, $4 a partir de uma recarga de $200, $3 a partir de uma recarga de $600 e $2 a partir de uma recarga de $1.000. Os preços aqui são em dólares americanos, e na moeda local no Canadá, na Austrália, em Israel, na Polônia, na Suíça, no Japão, na Coreia do Sul, em Taiwan, em Hong Kong, na Tailândia, em Singapura, na Índia, no restante da Europa e no Reino Unido; IVA ou impostos sobre vendas são tratados no checkout. Conectar um ATS e criar entrevistas é gratuito, e os 3 primeiros candidatos da sua primeira empresa são gratuitos. Veja os [preços](/pricing).

## Leitura relacionada

- [Como fazer a triagem de 100 candidatos em um dia](/guides/screen-100-applicants-in-a-day)
- [Testes de habilidades x triagem de currículos](/guides/skills-tests-vs-cv-screening)
- [Teste de seleção: guia prático](/pre-employment-testing)
