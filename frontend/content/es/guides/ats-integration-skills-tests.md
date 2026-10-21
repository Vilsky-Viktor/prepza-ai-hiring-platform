---
title: "Cómo conectar las pruebas de habilidades a tu ATS"
seoTitle: "Cómo conectar pruebas de habilidades a tu ATS: guía práctica"
description: "Envía pruebas de habilidades y recibe los resultados en tu ATS de forma automática, deja las decisiones en manos de personas y sabe qué revisar primero."
updated: "2026-10-21"
---

# Cómo conectar las pruebas de habilidades a tu ATS

La mayoría de los equipos de selección gestionan a los candidatos en un sistema de seguimiento de candidatos (ATS) y hacen las pruebas de habilidades en otra herramienta. Sin un vínculo entre ambos, alguien copia los correos del ATS, envía las invitaciones a mano, espera y luego vuelve a copiar las puntuaciones. Con cinco candidatos funciona. Con cincuenta, las invitaciones salen tarde, los resultados se quedan en una segunda pestaña que nadie abre y los buenos candidatos aceptan otras ofertas mientras esperan.

Esta guía explica qué hace una buena conexión entre un ATS y una herramienta de evaluación, qué revisar antes de confiar en ella y cómo configurarla para que la automatización se encargue del trabajo repetitivo mientras las personas siguen tomando cada decisión de contratación.

## Por qué conectarlos

| Sin conexión | Con conexión |
| --- | --- |
| Alguien exporta o copia los correos de los candidatos | Mover a un candidato a una etapa envía la invitación |
| Las invitaciones salen cuando alguien tiene tiempo | Las invitaciones salen a los pocos minutos del cambio |
| Los resultados se quedan en la herramienta de evaluación | Los resultados aparecen en la ficha del candidato en el ATS |
| Los responsables de contratación preguntan "¿alguien lo ha evaluado ya?" | El ATS muestra a quién se evaluó y cómo le fue |
| Errores en los correos y candidatos olvidados | El ATS es la única lista de quienes han presentado su candidatura |

La rapidez importa más de lo que parece. Cuanto más tiempo pasa entre la candidatura y la respuesta, más candidatos abandonan o aceptan otro trabajo. Las tasas exactas de abandono varían mucho según el puesto y el mercado, así que toma las cifras publicadas con cautela, pero la tendencia es constante: un proceso lento pierde gente, y los mejores candidatos suelen ser los que más opciones tienen.

## Cómo es un buen flujo

Una buena integración sigue las etapas que ya usas. No inventa un proceso nuevo.

1. **Un candidato presenta su candidatura** y llega a tu ATS como siempre.
2. **Una persona lo mueve a una etapa de evaluación,** por ejemplo "Prueba de habilidades". Ese cambio es el disparador, así que una persona sigue decidiendo a quién se evalúa.
3. **La herramienta de evaluación envía la invitación** automáticamente, para la prueba vinculada a esa vacante.
4. **El candidato hace la prueba** cuando le venga bien, dentro del plazo que fijes.
5. **Los resultados se registran en el candidato dentro del ATS:** la puntuación, si aprobó, las alertas de integridad y un enlace a todas sus respuestas.
6. **Una persona revisa el resultado** y hace avanzar al candidato, o no.

Dos cosas siguen siendo manuales a propósito: elegir a quién se evalúa y decidir qué pasa después. La conexión solo elimina el copiado intermedio.

### ¿Por qué no disparar con cada nueva candidatura?

Algunas herramientas invitan a todos los que presentan su candidatura. Puede estar bien en puestos de alto volumen donde todos hacen la misma prueba. Pero una etapa a la que mueves candidatos es más fácil de controlar: puedes saltarte a quienes claramente no cumplen un requisito indispensable (sin permiso de trabajo, ubicación equivocada) y nunca evalúas, ni pagas, a alguien a quien ibas a descartar de todos modos.

## Qué revisar antes de elegir una integración

No todos los "se integra con tu ATS" significan lo mismo. Haz estas preguntas antes de conectar nada.

| Pregunta | Por qué importa | Una buena respuesta |
| --- | --- | --- |
| ¿Cómo se conecta? | Las contraseñas compartidas y las cuentas en manos del proveedor son difíciles de auditar o revocar | Una clave API o un token que tu empresa crea y puede eliminar en cualquier momento |
| ¿Qué puede hacer la clave? | Una clave con acceso total es un riesgo si se filtra | Los permisos mínimos que necesita la integración, indicados en la documentación |
| ¿Qué dispara una invitación? | Necesitas saber exactamente cuándo reciben un correo los candidatos | Una etapa concreta que eliges para cada vacante |
| ¿Dónde llegan los resultados? | Unos resultados que nadie ve no ayudan | En el perfil del candidato, como una nota o un comentario que tu equipo ya lee |
| ¿Qué pasa si falla una invitación? | Sin créditos, un error tipográfico, una cuenta en pausa: candidatos atascados sin que nadie lo note | Se avisa a alguien y se puede volver a invitar al candidato |
| ¿Se puede procesar un evento dos veces? | Los ATS reenvían eventos; un candidato no debería recibir dos invitaciones | Cada candidato recibe una sola invitación por prueba, llegue el evento las veces que llegue |
| ¿Cómo se verifican los eventos entrantes? | A una dirección sin verificar se le pueden enviar eventos falsos | Solicitudes firmadas que la herramienta comprueba |
| ¿Cuánto tiempo se guardan los datos de los candidatos? | Leyes de privacidad como el RGPD exigen un plazo de conservación claro | Un límite declarado y la eliminación cuando borras la vacante, la prueba o tu cuenta |
| ¿Cuánto cuesta? | Los planes por usuario pueden encarecer la automatización | Un coste que puedes prever por cada candidato evaluado |

Si el proveedor no sabe responder con claridad a las preguntas sobre fallos y duplicados, prepárate para descubrirlo por las malas.

### Protección de datos

Conectar dos sistemas implica que los datos de los candidatos, al menos nombres y correos, pasan de una empresa a otra. Según el RGPD y leyes similares, tu proveedor de pruebas suele ser tu encargado del tratamiento, así que necesitas un contrato de encargo de tratamiento y debes informar a los candidatos, en tu aviso de privacidad o en la invitación, de que una prueba de habilidades forma parte del proceso. Comparte solo los datos que la prueba necesita. Para saber más sobre el lado legal de las pruebas y la IA en la selección de personal, consulta [¿Es legal usar IA en la selección de personal en la UE?](/guides/is-ai-hiring-legal-in-the-eu)

## Lista de comprobación para la configuración

Antes de activarla para una vacante real:

1. **Crea en tu ATS una etapa solo para la evaluación,** como "Prueba de habilidades". No reutilices una etapa que signifique otra cosa, o se invitará a candidatos por error.
2. **Crea la clave desde una cuenta de administrador** que vea todas las vacantes que quieres vincular, solo con los permisos que indica la documentación.
3. **Vincula cada vacante a su prueba** y elige la etapa que dispara la invitación.
4. **Configura el webhook** si tu ATS exige hacerlo a mano, y pega su secreto donde lo pida la herramienta.
5. **Pruébalo contigo.** Añade un candidato con tu propio correo, muévelo a la etapa, haz la prueba y comprueba que la nota aparece en el ATS.
6. **Decide quién vigila los fallos:** a quién se avisa cuando no se puede enviar una invitación y quién lo soluciona.
7. **Acuerda con tu equipo cómo se interpretan los resultados.** Una nota mínima es una orientación, no un descarte automático. Decídelo antes de que lleguen los resultados, no después.

## Errores comunes

- **Automatizar la decisión, no el papeleo.** Descartar automáticamente a todos los que no llegan a una puntuación elimina la revisión humana que detecta una pregunta mal planteada o a un candidato que tuvo problemas de conexión. Que la puntuación ordene; que una persona decida.
- **Disparar desde la etapa equivocada.** Una etapa que los reclutadores usan para otras cosas envía pruebas a personas que no deberían recibirlas.
- **Una sola prueba para todas las vacantes.** La conexión facilita enviar la misma prueba a todas partes. Una prueba ayuda más cuando está hecha para el puesto en cuestión. Consulta [Pruebas de habilidades frente a filtrado de CV](/guides/skills-tests-vs-cv-screening).
- **Nadie vigila los fallos.** Si una invitación falla sin avisar, el candidato espera un correo que nunca llega y tú crees que lo ignoró.
- **Una clave ligada a alguien que se va.** Algunas claves de ATS actúan en nombre de la persona que las creó. Cuando se cierra su cuenta, la conexión deja de funcionar. Usa una cuenta que vaya a seguir existiendo y vuelve a conectar cuando las personas cambien de puesto.
- **Olvidar a los candidatos que no están en el ATS.** Las recomendaciones y las candidaturas directas que nunca entran en el ATS también necesitan una invitación. Mantén también una forma manual de invitarlos.

## Cómo lo hace prepza

prepza se conecta con **Workable, Greenhouse, Teamtailor, Recruitee y Breezy HR** y sigue el flujo descrito arriba.

- **Tu clave, tu control.** Un propietario o administrador conecta el ATS en la pestaña Integraciones de la empresa con una clave que tu empresa crea en el ATS. prepza la comprueba antes de guardarla, la guarda cifrada y no vuelve a mostrarla. Al desconectar se eliminan al instante la clave y las vacantes vinculadas.
- **Vincula una vacante a una entrevista.** Elige una vacante del ATS y la etapa que dispara la invitación, y vincúlala a una entrevista de prepza existente o crea una nueva a partir del texto de la vacante en el ATS. Revisas los temas antes de que se escriba ninguna pregunta.
- **Mueves al candidato y sale la invitación.** Cada candidato recibe una sola invitación por entrevista, aunque el ATS envíe el mismo evento dos veces.
- **Resultados de vuelta en el ATS.** Cuando un candidato termina, prepza le añade en el ATS una nota o un comentario con su calificación, si aprobó, las alertas de integridad (salir de la página, intentos de copiar, respuestas elegidas demasiado rápido para haber leído la pregunta) y un enlace a su ficha de evaluación con todas las respuestas.
- **Los fallos no pasan desapercibidos.** Si no se puede invitar a un candidato, por ejemplo porque la empresa se ha quedado sin créditos, ha alcanzado un límite de correos, o porque prepza ha pausado las invitaciones temporalmente, todos los miembros de la empresa reciben una notificación que indica el ATS. Los candidatos no invitados por falta de créditos se invitan automáticamente después de una recarga, y los candidatos pendientes de cualquier vacante se pueden volver a invitar con un clic.
- **Slack, si lo usas.** prepza puede publicar notificaciones, como un candidato que ha terminado o un candidato del ATS al que no se pudo invitar, en el canal de Slack que elijas.
- **Tu propia plataforma.** Si tu ATS no está en la lista, la [API](/api-docs) de prepza te permite invitar a candidatos con una clave API y recibir un webhook firmado cuando un candidato empieza, termina, no recibe la invitación, su invitación caduca o se le elimina, y cuando una entrevista está lista.
- **Datos guardados durante un tiempo fijo.** Los candidatos que llegan desde un ATS se eliminan a los 365 días, o antes junto con su entrevista o su empresa.

Algunos ATS necesitan un paso por su lado. Greenhouse, Teamtailor y Recruitee te piden añadir un webhook a mano; el diálogo Instrucciones de prepza muestra la dirección y dónde pegar su secreto. prepza configura por sí mismo los webhooks de Workable y Breezy HR.

El precio es por candidato, sin suscripción: solo pagas por los candidatos que responden al menos una pregunta, $5 cada uno con la recarga de $50, $4 a partir de una recarga de $200, $3 a partir de una recarga de $600 y $2 a partir de una recarga de $1000. Los precios están en dólares estadounidenses, en euros en Europa (con las mismas cifras) y en libras en el Reino Unido (de £4 a £1,50); el IVA o los impuestos sobre las ventas se gestionan al pagar. Conectar un ATS y crear entrevistas es gratis, y los 3 primeros candidatos de tu primera empresa son gratis. Consulta los [precios](/pricing).

## Lecturas relacionadas

- [Cómo filtrar 100 candidatos en un día](/guides/screen-100-applicants-in-a-day)
- [Pruebas de habilidades frente a filtrado de CV](/guides/skills-tests-vs-cv-screening)
- [Pruebas de selección de personal: guía práctica](/pre-employment-testing)
