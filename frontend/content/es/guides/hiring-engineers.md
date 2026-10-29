---
title: "Cómo contratar ingenieros: un proceso estructurado de la descripción del puesto a la oferta"
seoTitle: "Cómo contratar ingenieros: proceso de selección estructurado"
description: "Proceso paso a paso para contratar ingenieros de software: perfil del puesto, filtrado, prueba de conocimientos, código, diseño, entrevistas y oferta."
updated: "2026-10-29"
---

# Cómo contratar ingenieros: un proceso estructurado de la descripción del puesto a la oferta

Contratar ingenieros es caro de una forma que es fácil pasar por alto: la mayor parte del coste es el tiempo de tus propios ingenieros. Cada hora que dedican a entrevistar a alguien que no conoce el stack es una hora que no dedican a construir. Un buen proceso pone primero las comprobaciones baratas y amplias, y reserva las caras y profundas para las pocas personas con más probabilidades de éxito.

Esta guía recorre ese proceso paso a paso. Se apoya en la investigación sobre selección donde la investigación es clara, y lo indica donde no lo es.

## El proceso de un vistazo

| Fase | Qué comprueba | Quién dedica tiempo |
| --- | --- | --- |
| 1. Perfil del puesto y descripción del puesto | Lo que el puesto realmente necesita | Responsable de contratación, un ingeniero sénior |
| 2. Filtrado de CV o candidaturas | Solo requisitos imprescindibles | Reclutador o responsable de contratación |
| 3. Filtro de conocimientos | Lo que el candidato sabe de tu stack | El candidato; tú lees los resultados |
| 4. Prueba para casa o programación en directo | Si sabe escribir código que funcione | Uno o dos ingenieros |
| 5. Diseño de sistemas (puestos sénior) | Cómo razona sobre sistemas más grandes | Un ingeniero sénior |
| 6. Entrevista conductual estructurada | Cómo trabaja con otras personas | Responsable de contratación, un compañero |
| 7. Comprobación de referencias | Confirmar lo que has oído | Responsable de contratación |
| 8. Decisión y oferta | Una decisión justa y documentada | El equipo de selección |

## Lo que dice la investigación

Las grandes revisiones de la investigación sobre selección comparan los métodos según lo bien que sus resultados se relacionan con el desempeño laboral posterior. La revisión importante más reciente, de Sackett, Zhang, Berry y Lievens (2022), corrigió a la baja las estimaciones anteriores y concluyó que los mejores predictores en promedio eran todos medidas específicas del puesto ([doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)). Sus estimaciones, en una escala en la que 0 significa ninguna relación y 1 una relación perfecta:

| Método | Validez estimada |
| --- | --- |
| Entrevistas estructuradas | .42 |
| Pruebas de conocimientos del puesto | .40 |
| Pruebas de muestra de trabajo | .33 |
| Entrevistas no estructuradas | .19 |
| Años de experiencia en el puesto | .07 |

De ahí se desprenden tres lecciones para la contratación de ingenieros:

- **La estructura importa más que el formato.** La misma entrevista con preguntas fijas y una guía de puntuación predijo mucho mejor que una conversación sin estructura.
- **Los años de experiencia dicen poco por sí solos.** «Cinco años de Java» es una señal débil comparada con lo que alguien realmente sabe y sabe hacer.
- **Combina métodos.** Ningún método predice lo bastante bien como para usarse solo.

Son promedios de muchos puestos y estudios, no garantías para tu puesto. Los autores también señalan que las pruebas de conocimientos y las muestras de trabajo son adecuadas para puestos en los que se espera que los candidatos ya tengan formación o experiencia. Eso encaja con la mayoría de las contrataciones de ingeniería, pero no con unas prácticas de aprendiz.

## Paso 1: Redacta un perfil del puesto y una descripción del puesto claros

Antes de publicar nada, escribe qué hará la persona en sus primeros seis meses y qué debe saber el primer día. Sé concreto:

- **Debe saber:** «Escribe y revisa consultas de PostgreSQL, incluidos joins e índices» se puede evaluar. «Buenos conocimientos de bases de datos», no.
- **Aprenderá en el puesto:** tus herramientas internas, tu dominio de negocio, las partes del stack que vas a enseñar.
- **Nivel:** qué distingue en tu equipo a una contratación de nivel medio de una sénior, como hacerse cargo de un servicio de principio a fin o liderar decisiones de diseño.

Acuérdalo con todas las personas implicadas en la contratación. Después, redacta la descripción del puesto a partir de ello. Una descripción del puesto que se corresponde con el trabajo real atrae a las personas adecuadas y facilita la preparación de cada paso posterior, porque cada prueba y cada entrevista se pueden vincular a ella.

Mantén corta la lista de «deseables». Las listas largas de requisitos echan para atrás a personas cualificadas que no cumplen todas las casillas.

## Paso 2: Filtra los CV solo por requisitos imprescindibles

Usa el CV o la candidatura para comprobaciones de sí o no: permiso de trabajo, ubicación o zona horaria si el puesto lo requiere, un idioma necesario y cualquier requisito sin el que el puesto realmente no pueda funcionar.

No clasifiques a las personas por su CV. Los cargos, los nombres de los empleadores y los años de experiencia son predictores débiles, y los CV son difíciles de comparar de forma justa: un CV potente puede reflejar tanto una buena redacción como un buen trabajo. Trata el CV como un filtro para lo que no se puede evaluar, y pasa a todos los que lo superen al filtro de conocimientos.

## Paso 3: Haz un filtro de conocimientos breve

Este es el paso que más tiempo ahorra a tus ingenieros. Antes de que nadie pase una hora en una entrevista en directo, comprueba qué sabe cada candidato de tu stack.

Un buen filtro de conocimientos es:

- **Específico del puesto:** evalúa los lenguajes, frameworks, bases de datos y prácticas de tu perfil del puesto, no curiosidades genéricas.
- **Breve:** unos pocos temas con unas 10 preguntas cada uno, para que los candidatos fuertes con otras ofertas lo terminen igualmente.
- **Igual para todos:** los mismos temas, el mismo número de preguntas y los mismos tiempos límite.

Aquí es donde encaja prepza. Convierte tu descripción del puesto en una entrevista de conocimientos de opción múltiple con tiempo límite. Revisas los temas propuestos antes de que se redacte ninguna pregunta, así que la prueba cubre tu stack y nada más. Para un puesto de ingeniería, puede incluir:

- **Preguntas de lectura de código:** un breve fragmento de código con preguntas sobre qué imprime o devuelve, qué hace, por qué falla o qué cambio lo corrige.
- **SQL:** una tabla pequeña y una consulta, con la pregunta de qué filas devuelve.
- **Conocimientos de arquitectura y frameworks:** compromisos de diseño, cómo se comporta un framework, qué falla bajo carga.

Cada candidato recibe su propio conjunto aleatorio de preguntas con una cuenta atrás en cada una. Ves una ficha de evaluación con cada respuesta y cuánto tardó, además de alertas de respuestas demasiado rápidas, salidas de la página, intentos de copiar y patrones inusuales en sus respuestas y tiempos. Una alerta es un motivo para mirar con más atención, no una prueba de nada. El informe también sugiere preguntas que acertó, para preguntarle por ellas en la siguiente entrevista.

Lo que prepza no hace: los candidatos no escriben, ejecutan ni depuran código en prepza. Leer código y escribirlo son habilidades distintas, así que el siguiente paso sigue siendo importante. Consulta las [pruebas de habilidades por puesto](/tests) para empezar desde pruebas ya preparadas.

## Paso 4: Prueba para casa o programación en directo

Ahora comprueba si los candidatos saben escribir código que funcione. Esta es la fase para escribir, ejecutar y depurar código, ya sea con tu propio ejercicio o en una plataforma para desarrolladores. Consulta [Alternativas a HackerRank](/compare/hackerrank-alternatives) para ver cómo encajan un filtro de conocimientos y una plataforma de programación.

Dos formatos habituales:

- **Prueba para casa:** realista y con poca presión, pero ocupa las tardes de los candidatos. Limítala a unas pocas horas como máximo, indica cuánto debería llevar y revísala con una rúbrica escrita.
- **Programación en directo:** más corta y más difícil de externalizar, pero más estresante. Programad en pareja sobre un problema realista, deja que los candidatos usen el lenguaje que mejor conocen y valora su razonamiento, no solo si terminan.

En ambos casos, puntúa con criterios acordados de antemano: corrección, legibilidad, pruebas, cómo gestionan los casos límite. Como el filtro de conocimientos ya ha reducido el grupo, haces este paso con un puñado de personas en lugar de con todas.

## Paso 5: Diseño de sistemas para puestos sénior

Para ingenieros sénior, añade una conversación de diseño: «¿Cómo construirías un servicio que haga X?». Fíjate en cómo aclaran los requisitos, cómo eligen entre alternativas y cómo detectan los puntos de fallo. Rara vez hay una única respuesta correcta, así que una rúbrica es imprescindible. Escribe cómo es una respuesta débil, sólida y fuerte antes de la primera entrevista.

Sáltate este paso en los puestos junior, donde sobre todo mide la seguridad en uno mismo más que la habilidad.

## Paso 6: Entrevistas conductuales estructuradas con rúbricas

Las entrevistas estructuradas fueron el mejor predictor individual en Sackett et al. (2022). Estructura significa:

- **Las mismas preguntas para todos los candidatos,** vinculadas al perfil del puesto: «Cuéntame una ocasión en la que no estuviste de acuerdo con una decisión de diseño. ¿Qué hiciste?».
- **Una rúbrica de puntuación para cada pregunta,** con ejemplos de respuestas débiles, sólidas y fuertes.
- **Puntuaciones independientes:** cada entrevistador puntúa antes de comentarlo con los demás, para que la opinión más ruidosa no decida el resultado.

Usa esta fase para lo que las pruebas no pueden mostrar: colaboración, sentido de responsabilidad, cómo recibe el feedback, cómo se comunica con personas que no son ingenieras.

## Paso 7: Comprobación de referencias

Las referencias pueden confirmar lo que has aprendido y sacar a la luz preocupaciones, pero trátalas como una comprobación final, no como una prueba decisiva. Sackett et al. no dieron una estimación de validez para la comprobación de referencias porque la investigación disponible era demasiado escasa, así que hay poca evidencia sobre lo bien que predicen el desempeño. Si las haces, plantea a cada referencia las mismas pocas preguntas sobre comportamientos concretos.

## Paso 8: Experiencia del candidato y tiempo hasta la oferta

Los buenos ingenieros suelen tener varios procesos abiertos a la vez. Un proceso lento o confuso hace que los pierdas.

- **Explica a los candidatos todo el proceso desde el principio:** las fases, cuánto dura cada una y cuándo tendrán noticias.
- **Mantenlo corto.** Programa las últimas fases próximas entre sí y decide poco después de la última entrevista.
- **Respeta su tiempo.** Un filtro de conocimientos breve al principio significa que menos personas pasan por entrevistas largas que difícilmente iban a superar.
- **Da una respuesta a tiempo a todos,** incluidas las personas que no siguen adelante.

## Equidad en todo el proceso

Un proceso estructurado también es más justo, pero solo si lo aplicas de forma coherente:

- **Preguntas coherentes** en cada fase, para todos los candidatos del mismo puesto.
- **Rúbricas escritas de antemano,** para que todos sean juzgados con los mismos criterios.
- **Adaptaciones:** ofrece tiempo extra u otro formato a los candidatos que lo pidan, por ejemplo por una discapacidad. En prepza, puedes dar tiempo extra a un candidato antes de que empiece.
- **Supervisa los resultados.** Los distintos métodos muestran diferencias de puntuación distintas entre grupos. Sackett et al. encontraron diferencias medias mayores en las pruebas de conocimientos del puesto y las muestras de trabajo que en las entrevistas estructuradas, lo que es un motivo más para combinar métodos. Vigila las tasas de aprobados en cada fase.
- **Deciden las personas.** Una puntuación respalda una decisión; no la toma. Mira las respuestas antes de rechazar a nadie.

Para lo básico en materia legal, incluido el Reglamento de IA de la UE (EU AI Act) y las normas estadounidenses sobre tasas de selección, consulta [Pruebas de selección de personal](/pre-employment-testing).

## Resumen

Pon primero las comprobaciones amplias y baratas, y al final las profundas y caras. Filtra los CV por requisitos imprescindibles, haz un filtro de conocimientos breve y después dedica el tiempo de los ingenieros a programación, diseño y entrevistas estructuradas con los pocos que queden. Puntúa con rúbricas escritas de antemano y mantén el proceso rápido y claro.

## Fuentes

- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection: Addressing systematic overcorrection for restriction of range. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## Lecturas relacionadas

- [Pruebas de habilidades por puesto](/tests)
- [Alternativas a HackerRank](/compare/hackerrank-alternatives)
- [Guía de pruebas de selección de personal](/pre-employment-testing)
- [Pruebas de habilidades frente a filtrado de CV](/guides/skills-tests-vs-cv-screening)
- [Entrevistar a ingenieros en la era de la IA](/guides/interviewing-in-the-age-of-ai)
