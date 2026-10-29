---
title: "Agentes de IA, MCP y API: qué son y cómo usarlos en la selección de personal"
seoTitle: "Agentes de IA, MCP y API en selección de personal"
description: "Qué son un agente de IA, MCP y una API, cómo usarlos con seguridad al contratar y cómo usar prepza con su asistente de IA, Claude, ChatGPT o tu plataforma."
updated: "2026-10-22"
---

# Agentes de IA, MCP y API: qué son y cómo usarlos en la selección de personal

La mayoría de la gente conoció la IA como una ventana de chat: preguntas y te responde. Un agente de IA va un paso más allá. Puede consultar información en tus herramientas y, cuando se lo pides, hacer cosas en ellas: crear una entrevista, invitar a una lista de candidatos, decirte quién sacó la mejor nota la semana pasada. El Model Context Protocol (MCP) es el estándar que permite que el chat de IA que ya usas, como Claude o ChatGPT, se conecte a herramientas como estas. Y una API es la forma más antigua y precisa de que un software hable con otro, sin IA de por medio.

Esta guía explica las tres cosas de forma sencilla, para qué sirven en la selección de personal, qué hay que vigilar y cómo usarlas con prepza.

## Qué es un agente de IA

Un chatbot solo escribe texto. Un agente es un modelo de lenguaje con **herramientas**: acciones pequeñas y bien definidas que puede usar, como «listar los candidatos de esta entrevista» o «invitar a este correo». Cuando le preguntas algo, el agente decide qué herramientas usar, lee lo que devuelven y responde a partir de eso, no de memoria.

| Un chatbot | Un agente de IA |
| --- | --- |
| Responde con lo que aprendió en su entrenamiento | Responde con tus datos actuales, leídos a través de herramientas |
| Solo puede describir cómo se hace algo | Puede hacerlo, cuando se lo pides y lo permites |
| Se lo inventa cuando no lo sabe | Lo consulta, o dice que no puede |
| Vive en una sola ventana | Trabaja dentro de las herramientas a las que lo conectas |

Las herramientas son lo que hace útil a un agente, y también lo que lo hace seguro o no. Un buen agente solo puede usar las herramientas que se le dan, solo con tus permisos, y solo hace lo que pediste.

## Qué es MCP

El Model Context Protocol es un estándar abierto que Anthropic presentó a finales de 2024 y que hoy admiten Claude, ChatGPT y muchas otras apps de IA y herramientas para desarrolladores. Se suele comparar con un puerto USB-C para la IA: en lugar de que cada app de IA construya su propia conexión con cada herramienta, una herramienta ofrece un único **servidor MCP**, y cualquier app de IA que hable MCP puede usarlo.

Un servidor MCP le dice tres cosas a la app de IA:

1. **Qué herramientas existen**, con un nombre, una descripción y los datos que necesita cada una.
2. **Qué herramientas solo leen** y cuáles cambian algo, para que la app de IA pueda preguntarte antes de un cambio.
3. **Quién eres**, mediante un inicio de sesión que apruebas una sola vez, para que cada llamada se haga en tu nombre y con tus permisos.

Para ti, esto significa que puedes trabajar con una herramienta desde el chat que ya usas, sin copiar datos de una ventana a otra.

## Qué es una API y en qué se diferencia

Una API (interfaz de programación de aplicaciones) es un conjunto de peticiones fijas que un programa puede enviar a otro: «listar los candidatos de esta entrevista», «invitar a este correo». Tus desarrolladores escriben el código que las envía. No interviene ninguna IA: la misma petición siempre hace lo mismo, que es justo lo que quieres en una automatización que funciona sola.

| | Mira, la asistente de IA (en la app) | MCP (en Claude o ChatGPT) | API |
| --- | --- | --- | --- |
| Quién lo usa | Tú, en prepza | Tú, en tu chat de IA | El código de tu plataforma |
| Cómo se pide | Con tus propias palabras | Con tus propias palabras | Peticiones fijas que escribe un desarrollador |
| Quién aprueba los cambios | Tú, en una tarjeta | Tú, en tu app de IA | Tu código, tal como está escrito |
| Ideal para | Preguntas y tareas rápidas | Combinar prepza con tus otras herramientas y archivos | Automatizaciones que funcionan sin que nadie las vigile |
| Inicia sesión como | Tú | Tú | Una clave de la empresa |

Usa Mira o MCP cuando haya una persona en el proceso. Usa la API cuando tu propio sistema deba invitar a candidatos y recoger los resultados por sí solo, por ejemplo desde una web de empleo o una herramienta interna de RR. HH.

## Para qué sirve en la selección de personal

La selección de personal tiene muchos pasos pequeños y repetitivos repartidos entre herramientas. Un agente se maneja bien justo con eso:

- **Preguntas sobre tu proceso de selección.** «¿Qué candidatos de Senior Backend aprobaron esta semana?», «¿Quién no ha empezado aún su entrevista?», «¿Cuál es nuestra calificación media para el puesto de analista de datos?»
- **Configurar cosas.** «Crea una entrevista a partir de esta descripción del puesto», «Pon la nota de aprobado en 70 %», «Dale a este candidato un 50 % de tiempo extra».
- **Trabajo en bloque.** «Invita a estas 12 personas a la entrevista de frontend», pegado directamente de un correo o una hoja de cálculo.
- **Combinar fuentes.** En Claude o ChatGPT puedes combinar prepza con tus otras herramientas y archivos conectados: comparar una descripción del puesto de tus documentos con los temas de la entrevista, o redactar un mensaje para los candidatos preseleccionados.

Lo que no debe hacer es tomar la decisión de contratación. Una calificación apoya el criterio de una persona; no lo sustituye. Pide al agente que ordene, resuma y prepare, y deja la decisión en manos de una persona. Consulta [¿Es legal usar IA en la selección de personal en la UE?](/guides/is-ai-hiring-legal-in-the-eu) para ver por qué eso también importa legalmente.

## Qué hay que vigilar

Conectar una IA a tus datos de selección merece el mismo cuidado que dar acceso a un compañero.

| Riesgo | Qué ayuda |
| --- | --- |
| El agente hace algo que no querías | Los cambios necesitan antes tu aprobación, y solo hace lo que pediste |
| Ve más de lo que debería | Actúa en tu nombre: ve lo que tú ves, nada más |
| Instrucciones ocultas en los datos | Los nombres, respuestas y documentos de los candidatos son datos, nunca instrucciones que seguir |
| Secretos que acaban en un chat | Las claves API y las contraseñas nunca pasan por el chat |
| Errores irreversibles | Eliminar una cuenta o una empresa sigue estando en la app, tras su propia confirmación |
| Datos que salen de tus herramientas | Los datos llegan a la app de IA que conectas, según las condiciones de esa app: conecta solo apps que tu empresa permita |
| Uso descontrolado | Límites de cuántas acciones se ejecutan por hora |

Antes de conectar cualquier app de IA a datos de trabajo, revisa la política de tu empresa sobre herramientas de IA, e indica a los candidatos en tu aviso de privacidad qué servicios tratan sus datos.

## Tres formas de trabajar con prepza más allá de sus páginas

### 1. Mira, la asistente de IA integrada

Selecciona **preguntar a Mira** en la cabecera de cualquier página. Mira, la asistente de IA de prepza, conoce tus empresas, entrevistas, candidatos, créditos e integraciones, y cómo funciona prepza. Responde en tu idioma, y puedes escribir o hablar.

- **Responde con tus datos**, con la misma vista que tienes tú: un administrador ve lo que ve un administrador, un lector lo que ve un lector.
- **Sabe en qué página estás.** Pregunta «¿Qué puedo hacer en esta página?» para ver la guía de esa página, o «¿Quién es el mejor aquí?» en los candidatos de una entrevista, y responde sobre esa entrevista sin preguntarte cuál.
- **Prepara los cambios y tú los confirmas.** Si le pides invitar a candidatos, muestra una tarjeta con exactamente lo que va a pasar, por ejemplo «Invitar a 12 candidatos a Backend developer». No se ejecuta nada hasta que seleccionas Confirmar.
- **Muestra sus fuentes.** Debajo de una respuesta ves los candidatos o las entrevistas que usó y un enlace a la página de donde salen.
- **No se sale del tema.** Responde sobre prepza y la selección de personal con prepza, y declina lo demás.

### 2. prepza en Claude o ChatGPT, a través de MCP

Si tu equipo ya trabaja en Claude o ChatGPT, puedes llevar prepza allí. El servidor MCP de prepza ofrece las mismas herramientas que Mira, la asistente integrada.

**Para conectarlo:**

1. En prepza, abre la pestaña **Integraciones** de una empresa y selecciona **Apps de IA**. Copia la dirección del servidor: `https://prepza.ai/mcp`.
2. **En Claude:** abre Configuración, luego Conectores, y añade un conector personalizado con esa dirección. **En Claude Code:** ejecuta `claude mcp add --transport http prepza https://prepza.ai/mcp`. **En ChatGPT:** añádelo como conector personalizado en su configuración de apps y conectores.
3. Tu app de IA abre el inicio de sesión de prepza. Inicia sesión, comprueba qué app lo solicita y selecciona **Permitir**. Para que solo pueda leer, desactiva antes **Permitir cambios**.

A partir de ahí, pregunta en tu chat como le preguntarías a un compañero: «En prepza, ¿quiénes son los tres mejores candidatos para Product designer?». La mayoría de las apps de IA te preguntan antes de un cambio y te avisan antes de cualquier cosa que no se pueda deshacer: prepza les indica qué acciones cambian o eliminan algo.

**Lo que se mantiene igual que en la app:**

- **Tus permisos.** Actúa en tu nombre, en cada empresa de la que formas parte, con tu rol en cada una.
- **Créditos y límites.** Invitar a un candidato cuesta lo mismo que en la app, y se aplican los mismos límites de correos.
- **El registro.** Todo lo que una app de IA hace por ti aparece en el registro de acciones de la empresa como hecho a través de una app de IA, desde aprobar temas y ver resultados hasta dar tiempo extra o revocar a un candidato. El propietario de la empresa lo consulta en la pestaña **Registro de acciones** de la empresa.
- **La empresa decide.** Los propietarios y administradores pueden impedir que las apps de IA usen los datos de una empresa con **Permitir apps de IA en esta empresa** en su página de apps de IA.
- **Lo que no puede hacer.** No puede ver tu contraseña ni tus claves API, y no puede eliminar tu cuenta ni una empresa. Eso se queda en la app.

**Para desconectarlo,** elimina el conector en tu app de IA, o selecciona **Desconectar** junto a él en **Apps de IA**, en la pestaña Integraciones. Deja de funcionar al instante.

**Otras apps y tus propios agentes.** La [pestaña MCP](/api-docs?tab=mcp) de la documentación para desarrolladores tiene los pasos para Gemini CLI, Cursor, VS Code y Le Chat, y agentes de ejemplo completos en Python y TypeScript. Un agente que se ejecuta en un servidor, sin nadie que apruebe un inicio de sesión, usa una clave de API de la empresa con el permiso **Usar con agentes de IA (MCP)**: solo funciona en esa empresa y solo con las herramientas que permiten los demás permisos de la clave.

### 3. Tu propia plataforma, a través de la API

Para automatizaciones sin IA, prepza tiene una API, descrita en su [documentación para desarrolladores](/api-docs).

1. Un propietario o administrador abre la pestaña **Integraciones** de una empresa, luego **API**, y selecciona **Nueva clave**. Ponle el nombre de la plataforma que la va a usar, elige cuándo caduca y marca solo lo que necesita: la clave de un panel solo lee; la de un portal de empleo también invita. Más adelante puedes añadirle o quitarle permisos. La clave se muestra una sola vez; guárdala en un lugar seguro.
2. Tu plataforma envía peticiones con esa clave: listar las entrevistas de la empresa, listar o consultar candidatos con su calificación, si aprobaron y sus alertas de integridad, e invitar a un candidato.
3. Añade un **webhook**: una dirección de tu plataforma a la que prepza llama, con firma, cuando un candidato empieza, termina, no recibe la invitación, su invitación caduca o se le elimina, y cuando una entrevista está lista, para que no tengas que estar preguntando. La página de la API puede enviarle un evento de prueba y muestra su registro de entregas.

Cada candidato incluye un enlace a sus resultados completos en prepza y, hasta que termina, su propio enlace de invitación, para que tu plataforma pueda enviarlo en su propio mensaje si lo prefieres. Cuando tu plataforma ya sabe quién es el candidato, invítalo sin inicio de sesión: prepza no envía correos y el candidato hace la entrevista desde el enlace sin iniciar sesión en prepza, así que envía el enlace solo a él. Una invitación también puede devolver al candidato a tu sitio con un botón en la página final y fijar un tema claro u oscuro con los colores de tu empresa. Con el SDK de prepza, tu propia página puede mostrar la entrevista. Devolver a los candidatos a tu sitio y mostrar la entrevista en él requiere una empresa verificada, y solo funciona en el dominio de su sitio web.

Se aplica la misma regla que en todo lo demás: la calificación apoya la decisión de una persona, así que no descartes candidatos automáticamente por ella.

## Cuál usar en cada caso

Parte de quién hace el trabajo y con qué frecuencia.

| Tu situación | Qué usar |
| --- | --- |
| Estás en prepza y quieres una respuesta rápida: quién aprobó, quién no ha empezado, cuántos créditos quedan | Mira, la asistente integrada |
| Quieres configurar algo en pocas palabras: una entrevista a partir de una descripción del puesto, una nota de aprobado, tiempo extra | Mira, la asistente integrada |
| Ya trabajas en Claude o ChatGPT todo el día y quieres tener prepza también ahí | MCP |
| La tarea necesita prepza y algo más: tus documentos, borradores de correo, otra herramienta conectada | MCP |
| Un reclutador fuera de la oficina quiere revisar el proceso desde la app de IA de su móvil | MCP |
| Tu web de empleo o tu sistema de RR. HH. debe invitar a candidatos por sí solo, sin que nadie haga clic | La API |
| Los resultados deben llegar a tu propia base de datos o panel en cuanto los candidatos terminan | La API, con un webhook |
| Tu ATS es uno de los que prepza conecta (Workable, Greenhouse, Teamtailor, Recruitee, Breezy HR) | Ninguno de estos: conecta el ATS en la pestaña Integraciones. Consulta [Cómo conectar las pruebas de habilidades a tu ATS](/guides/ats-integration-skills-tests) |

Una regla sencilla:

- **Una persona pregunta y revisa cada cambio:** Mira en prepza, o MCP si esa persona vive en Claude o ChatGPT.
- **Un software actúa por sí solo, siempre de la misma forma:** la API.
- **Para empezar:** prueba primero a Mira, la asistente integrada. No necesita configuración, y lo que aprendas te servirá para MCP.

También funcionan juntos. Un equipo puede enviar las invitaciones desde su sistema de RR. HH. a través de la API, mientras los reclutadores preguntan por los resultados a Mira o a su chat de IA.

## Cómo obtener buenos resultados

- **Llama a las cosas por su nombre.** «La entrevista de Senior Backend» funciona mejor que «esa entrevista».
- **Pide un paso cada vez** cuando importa. Revisa el resultado y luego pide el siguiente.
- **Lee la aprobación antes de permitirla.** Muestra exactamente lo que se va a ejecutar.
- **Pregunta de dónde sale una cifra.** Un buen agente puede señalar los candidatos o la página en los que se basa.
- **Deja las decisiones a las personas.** Usa el agente para buscar, ordenar y preparar; la decisión es tuya.

## Precios

Mira, la conexión MCP y la API son gratuitas. Solo pagas por candidatos, como siempre: por cada candidato que responde al menos una pregunta, sin suscripción. Consulta los [precios](/pricing).

## Lecturas relacionadas

- [Cómo conectar las pruebas de habilidades a tu ATS](/guides/ats-integration-skills-tests)
- [Entrevistar a ingenieros en la era de la IA](/guides/interviewing-in-the-age-of-ai)
- [¿Es legal usar IA en la selección de personal en la UE?](/guides/is-ai-hiring-legal-in-the-eu)
