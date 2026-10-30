# The FAQ in es; the {placeholders} are filled in by helpers/help.py (faq_values) with
# billing's prices and the number of languages. Questions not translated yet show in English
# (constants/faq/__init__.py).
FAQ = [
    {
        "key": "what",
        "question": "¿Qué es prepza?",
        "answer": "Una entrevista cronometrada creada a partir de tu descripción del puesto, para cualquier puesto. Úsala para filtrar candidatos antes de conocerlos o como un paso más de la contratación: en ambos casos ves quién domina de verdad el trabajo.",
    },
    {
        "key": "roles",
        "question": "¿Para qué puestos puedo contratar?",
        "answer": "Cualquier puesto en el que importen los conocimientos: soporte, ventas, finanzas, salud, oficios, ingeniería, marketing y más. Si puedes describir el trabajo, prepza puede crear una entrevista para él.",
    },
    {
        "key": "hiring",
        "question": "¿Cómo funciona?",
        "answer": "Pega una descripción del puesto en la página de inicio, pon el nombre de tu empresa y revisa los temas que propone prepza. Después invita a candidatos: escribe sus correos, pega una lista o sube un archivo. Los candidatos que no hayan empezado tras unos días reciben un recordatorio. Cada candidato recibe sus propias preguntas, cada una con su temporizador, y ves su puntuación y cada respuesta en cuanto termina.",
    },
    {
        "key": "link",
        "question": "¿Puedo poner una entrevista en una oferta de empleo?",
        "answer": "Sí. Activa el enlace para compartir de la entrevista en su pestaña Ajustes y pégalo en tu oferta. Cualquiera que lo abra inicia sesión y hace la entrevista, y cada persona cuesta lo mismo que un candidato invitado. El enlace se desactiva cuando marcas el puesto de la entrevista como cubierto.",
    },
    {
        "key": "preview",
        "question": "¿Puedo probar una entrevista antes de invitar a nadie?",
        "answer": "Sí. Abre tu entrevista como candidato desde su página, sin coste: las vistas previas no aparecen entre tus candidatos ni en las estadísticas de preguntas. También puedes hacer cualquiera de las entrevistas de práctica gratuitas.",
    },
    {
        "key": "open-to-offers",
        "question": "¿Pueden las empresas encontrarme a través de mi práctica?",
        "answer": "Solo si tú lo eliges. Activa Abierto a ofertas después de una ronda de práctica o en Ajustes, con la dirección de tu perfil de LinkedIn. Entonces, las empresas que contratan en prepza ven tu nombre, tu perfil de LinkedIn y tu último resultado de práctica en cada tema de sus entrevistas que hayas practicado, y pueden invitarte a una entrevista. prepza no te clasifica ni te recomienda. Desactívalo cuando quieras en Ajustes y desaparecerás al instante de la lista de todas las empresas; además, se desactiva un año después de la última vez que lo activaste o guardaste tu perfil de LinkedIn.",
    },
    {
        "key": "cheating",
        "question": "¿Pueden los candidatos usar IA o buscar las respuestas?",
        "answer": "Cada candidato recibe sus propias preguntas aleatorias en su propio orden, con [un temporizador en cada pregunta](/guides/skills-test-timing-and-extra-time) que controla nuestro servidor, así que hay poco tiempo para buscar las respuestas o preguntar a una IA. Las fichas de evaluación también muestran cuándo un candidato salió de la página, copió texto o respondió demasiado rápido para haber leído la pregunta. Cuando termina, su página también señala patrones de respuesta que suele dejar pasarle las preguntas a una IA, como más o menos el mismo tiempo en cada pregunta o preguntas difíciles acertadas mientras fallaba las fáciles, y sugiere preguntas que acertó para tratar en una entrevista en vivo. Un patrón es un motivo para preguntar, no una prueba. Antes de empezar, cada candidato también confirma que responderá por su cuenta, sin herramientas de IA ni ayuda de otras personas, y su ficha de evaluación lo muestra.",
    },
    {
        "key": "voice",
        "question": "¿Pueden los candidatos responder con la voz?",
        "answer": "Sí, si la empresa configura una entrevista en modo de voz (en inglés, español, alemán, francés, portugués o italiano). Las preguntas se leen en voz alta y los candidatos responden hablando; lo que dicen se convierte en texto y se asocia a una opción que ellos confirman, y nunca se guarda. Las voces no se analizan para detectar tono ni emociones, y los candidatos siempre pueden tocar una opción en su lugar.",
    },
    {
        "key": "cost",
        "question": "¿Cuánto cuesta?",
        "answer": "Generar entrevistas es gratis. Cada candidato que responde al menos una pregunta cuesta {candidate} créditos ({candidate_price}), y menos con créditos de recargas más grandes, hasta {cheapest_price}. Tu primera empresa recibe {company} créditos gratis, suficientes para sus primeros {company_candidates} candidatos. La [página de precios](/pricing) muestra todos los precios.",
    },
    {
        "key": "charged",
        "question": "¿Cuándo se cobra por un candidato?",
        "answer": "Una vez que ha respondido al menos una pregunta: cuando termina su entrevista (la termina él o se acaba el tiempo mientras está ausente) o cuando lo revocas. Una pregunta cuyo tiempo se agotó sin elegir respuesta no cuenta. Sus créditos se reservan al invitarlo y se devuelven si lo revocas antes de que responda nada, si nunca empieza o si su entrevista termina sin ninguna respuesta.",
    },
    {
        "key": "compare_hiring",
        "question": "¿Cómo se compara el precio con otras herramientas de evaluación?",
        "answer": "Muchas herramientas de evaluación se venden como suscripción mensual o anual, que pagas aunque no evalúes a nadie. Con prepza pagas solo por candidato: {candidate} créditos ({candidate_price}), sin contrato, sin cuotas por usuario y sin pagar por generar una entrevista. Una empresa que invita a {example_candidates} candidatos al mes paga unos {example_year_price} al año. Si evalúas a muchos candidatos cada mes, una suscripción puede salir más barata, así que compara con tus propias cifras.",
    },
    {
        "key": "expire",
        "question": "¿Caducan los créditos?",
        "answer": "No. Los créditos nunca caducan y no hay suscripciones de pago. Si activas la recarga automática opcional, Paddle guarda tu tarjeta como una suscripción de {zero_price}; solo pagas las recargas que haga.",
    },
    {
        "key": "currency",
        "question": "¿En qué moneda pago?",
        "answer": "Los precios están en la moneda local en Canadá, Australia, Israel, Polonia, Suiza, Japón, Corea del Sur, Taiwán, Hong Kong, Tailandia, Singapur e India; en euros en el resto de la UE y en Islandia, Liechtenstein y Noruega; en libras en el Reino Unido; y en dólares estadounidenses en el resto del mundo. Tu cuenta y cada empresa conservan la moneda del país donde se crearon, viajes a donde viajes: cambia la tuya en Ajustes, y la de una empresa junto a su botón «Recargar» (propietarios y administradores). Las recargas de una empresa, también las automáticas, se cobran siempre en la moneda de la empresa.",
    },
    {
        "key": "refunds",
        "question": "¿Puedo obtener un reembolso?",
        "answer": "Sí, de los créditos que compraste en los últimos 14 días y no has gastado: a través de Paddle o escribiéndonos. Los créditos gratis, como el regalo de bienvenida, no se reembolsan. Los [términos](/terms) tienen los detalles.",
    },
    {
        "key": "scorecards",
        "question": "¿Qué muestran las fichas de evaluación?",
        "answer": "Cada respuesta, si fue correcta y cuánto tardó. La nota es el porcentaje de puntos obtenidos: cada pregunta vale un punto, y una de «selecciona todas las correctas» da una parte por cada opción correcta marcada, y nada si se marca una incorrecta. Las notas se ven en verde o rojo según la nota de aprobado que fijaste para la entrevista. Las fichas también señalan respuestas demasiado rápidas para haber leído la pregunta, las veces que el candidato salió de la página y los intentos de copiar.",
    },
    {
        "key": "reports",
        "question": "¿Puedo compartir los resultados con un responsable de contratación?",
        "answer": "Sí. Descarga un informe PDF de un candidato o de todos los candidatos de una entrevista, envíalo por correo directamente desde prepza o manda un breve resumen por WhatsApp, Telegram, Viber o LINE.",
    },
    {
        "key": "action_log",
        "question": "¿Puedo ver quién hizo qué en mi empresa?",
        "answer": "Sí, si eres el propietario de la empresa. Su pestaña Registro de acciones muestra todo lo que hicieron sus miembros, de lo más reciente a lo más antiguo: invitar o quitar candidatos, ver resultados y cambiar las entrevistas, el equipo, la facturación y las integraciones, con quién lo hizo, cuándo y si lo hizo en su nombre el asistente, una app de IA o la API. Puedes filtrarlo por miembro, tipo de acción y fechas. Las acciones se guardan durante 12 meses. Las acciones de una clave de API aparecen con el nombre de la clave.",
    },
    {
        "key": "notes",
        "question": "¿Puede mi equipo dejar comentarios sobre una entrevista?",
        "answer": "Sí. Cada entrevista tiene una pestaña Comentarios donde tu equipo escribe comentarios en texto sin formato sobre el proceso de selección, como a quién llamar a continuación o, en una agencia, para qué cliente es la entrevista. Cualquier miembro puede escribir comentarios, también los lectores, y editar los suyos; pueden eliminar uno su autor, los propietarios y los administradores. Los propietarios y administradores pueden fijar un comentario, que entonces aparece bajo el nombre de la entrevista. Los candidatos nunca ven los comentarios.",
    },
    {
        "key": "integrations",
        "question": "¿prepza funciona con mi ATS u otras herramientas?",
        "answer": "Sí, sin coste adicional. Conecta Workable, Greenhouse, Teamtailor, Recruitee o Breezy HR en la pestaña Integraciones de tu empresa: los candidatos que muevas a una etapa reciben la entrevista, y sus resultados vuelven al ATS ([cómo conectar las pruebas de habilidades a tu ATS](/guides/ats-integration-skills-tests)). Slack puede publicar las notificaciones de tu empresa en un canal, y la API permite que tu propia plataforma cree entrevistas, invite y gestione candidatos y reciba sus resultados, con cada clave de API limitada a lo que marques para ella; consulta la [Documentación de la API](/api-docs).",
    },
    {
        "key": "ai_apps",
        "question": "¿Puedo usar prepza desde Claude, ChatGPT o mi propio agente de IA?",
        "answer": "Sí. Añade prepza a Claude o ChatGPT como conector (los pasos están en la pestaña Integraciones de tu empresa) y permítelo en prepza. A partir de ahí, la app trabaja con tus empresas, entrevistas y los resultados de los candidatos en tu nombre, con tus permisos; la mayoría de las apps te preguntan antes de cambiar nada. Tu cuenta o una empresa solo se eliminan en prepza. Lo que la app lee llega a su proveedor según las condiciones de esa app. Puedes desconectarla en cualquier momento en la misma pestaña. También se pueden conectar otras apps de IA y agentes que crees tú mismo: la [pestaña MCP](/api-docs?tab=mcp) de la documentación para desarrolladores tiene los pasos y agentes de ejemplo, y un agente en un servidor puede iniciar sesión con una clave de API que tenga el permiso de agentes de IA. La [guía sobre agentes de IA, MCP y API](/guides/ai-agents-mcp-and-api) explica para qué sirve cada uno.",
    },
    {
        "key": "candidates",
        "question": "¿Qué ven los candidatos?",
        "answer": "El nombre y el logo de tu empresa, con los colores y las fuentes de tu empresa (definidos en su pestaña Marca), qué esperar antes de empezar y luego una pregunta cronometrada cada vez. Nunca ven su puntuación ni si una respuesta fue correcta.",
    },
    {
        "key": "verified",
        "question": "¿Qué significa la marca de verificación?",
        "answer": "Que un propietario o administrador de la empresa inició sesión con un correo de trabajo del sitio web de la empresa, como tu@acme.com, y que después nuestro equipo revisó la empresa. Añade el sitio web con Verificar en la cabecera de tu empresa; los servicios de correo gratuitos no cuentan. Mientras la revisión está pendiente, tu equipo ve un reloj junto al nombre, y cambiar el nombre de la empresa la envía de nuevo a revisión. La marca aparece junto al nombre de tu empresa, también en las invitaciones.",
    },
    {
        "key": "languages",
        "question": "¿Qué idiomas se admiten?",
        "answer": "{count} idiomas, para el sitio, las entrevistas y los correos. Elige el idioma en que se escribe una entrevista, sea cual sea el idioma de la descripción del puesto.",
    },
    {
        "key": "privacy",
        "question": "¿Qué pasa con las descripciones de puesto y las respuestas?",
        "answer": "Las descripciones de puesto se usan para crear las entrevistas de tu empresa, y las respuestas de los candidatos, para puntuarlas para tu empresa. Las preguntas que genera prepza también pueden reutilizarse en las entrevistas y la práctica de otras empresas, sin nada que te identifique a ti, a tu empresa ni a ninguna otra persona; puedes excluir de esto las preguntas de una entrevista en sus ajustes. prepza también extrae, de cómo se responden las preguntas, patrones generales y anonimizados sobre su calidad para mejorar cómo se generan las preguntas. La [política de privacidad](/privacy) explica qué guardamos, durante cuánto tiempo y los derechos de cada persona.",
    },
    {
        "key": "eu_ai_law",
        "question": "¿Es legal usar IA en la preselección de candidatos en la UE?",
        "answer": "Sí, con normas. Según el Reglamento de IA de la UE (AI Act), las herramientas que puntúan a candidatos son muy probablemente de alto riesgo, con obligaciones desde el 2 de diciembre de 2027, y el RGPD ya se aplica: una persona toma la decisión de contratación, se informa a los candidatos de que se usa IA y se guardan registros. prepza funciona así: la IA redacta las preguntas, las personas de tu empresa revisan los resultados y deciden, y se informa a los candidatos antes de empezar. Esto no es asesoramiento jurídico; [¿Es legal usar IA en la selección de personal en la UE?](/guides/is-ai-hiring-legal-in-the-eu) explica las normas y las fechas.",
    },
    {
        "key": "uk_us",
        "question": "¿Podemos usar prepza con candidatos del Reino Unido y Estados Unidos?",
        "answer": "Sí. El acuerdo de tratamiento de datos cubre la legislación del Reino Unido y de Estados Unidos, y las instrucciones para empresas y las plantillas de aviso para candidatos (con versiones para la ciudad de Nueva York, Illinois y Colorado) cubren lo que debes comunicar a los candidatos. Para puestos en la ciudad de Nueva York, úsalo solo cuando hayas cumplido lo que te exige la Local Law 144: una auditoría de sesgos independiente en el año anterior a su uso, la publicación de su resumen y un aviso a los candidatos 10 días hábiles antes.",
    },
    {
        "key": "emails",
        "question": "¿Qué correos envía prepza y cómo dejo de recibirlos?",
        "answer": "Los correos del servicio, como invitaciones, informes, problemas de pago y cambios en nuestros términos, se envían siempre. El resto, como el resumen de actividad diario, los recordatorios y las novedades del producto, lo eliges en Ajustes, en Correos, o lo detienes con el enlace «Cancelar la suscripción» de cada correo. Los candidatos pueden dejar de recibir los correos de tu empresa, o los recordatorios de una entrevista, con los enlaces de sus invitaciones y recordatorios. Las novedades de prepza aparecen en tus notificaciones, la campana de arriba; las más importantes también llegan por correo como novedad del producto, solo mientras ese ajuste esté activado.",
    },
    {
        "key": "delete",
        "question": "¿Puedo eliminar mi cuenta?",
        "answer": "Sí, en Ajustes. Tu cuenta y tus datos se eliminan, y antes puedes descargar una copia de tus datos.",
    },
    {
        "key": "report",
        "question": "¿Cómo informo de un problema?",
        "answer": "Escríbenos desde la [página de contacto](/contact) y pega el ID de aquello de lo que se trate: «copiar id» está debajo del nombre de una empresa, una entrevista o un candidato, y el de tu cuenta, en el menú de tu cuenta y en Ajustes. Con el ID lo encontramos enseguida.",
    },
]
