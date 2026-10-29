---
title: "AI 时代如何面试工程师：现在应该考察什么"
seoTitle: "AI 时代的技术面试：现在应该考察什么"
description: "AI 编程助手已成为工程师日常工作的一部分。这如何改变技术面试应考察的内容、企业如何应对，以及知识笔试在流程中的位置。"
updated: "2026-10-29"
---

# AI 时代如何面试工程师：现在应该考察什么

多年来，经典的技术面试都要求候选人从零开始写代码：反转链表、实现一个缓存、在白板或共享编辑器里解一道题。背后的逻辑很简单：能写出代码的人，大概也能胜任这份工作。

AI 编程助手削弱了这种联系。如今很多常规代码，助手几秒钟就能写出初稿，工作中如此，远程面试中也是如此，除非你加以阻止。这并不意味着工程能力变得不重要了，而是改变了哪些能力最重要，因此也改变了面试应该考察什么。

本指南回顾发生了哪些变化、一些公司如何应对，以及如何设计一套仍能告诉你谁能胜任工作的面试流程。本文面向招聘经理和技术负责人。

## 发生了什么变化

AI 助手如今已是许多开发者日常工作的一部分。在 2025 年 Stack Overflow 开发者调查中，84% 的受访者表示在开发过程中使用或计划使用 AI 工具，51% 的专业开发者表示每天都在使用（[Stack Overflow，2025](https://survey.stackoverflow.co/2025/ai)）。GitHub 的 Octoverse 2025 报告称，GitHub 上 80% 的新开发者在第一周就使用了 Copilot（[GitHub，2025 年 10 月](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)）。

同一项调查也揭示了局限。不信任 AI 输出准确性的受访者（约 46%）多于信任的受访者（约 33%）。最常见的困扰是“AI 给出的方案几乎正确，但又不完全正确”，有 66% 的人提到；45% 的人表示调试 AI 生成的代码会花更多时间（[Stack Overflow，2025](https://survey.stackoverflow.co/2025/ai)）。

综合来看，这些数字描述了工作本身的转变：写出代码初稿的成本越来越低，而判断初稿是否正确、在出错时修好它，才是如今很大一部分能力所在。

## 企业如何应对

整个行业目前还没有统一的答案。公开报道的做法方向各异：

- **允许甚至要求在面试中使用 AI。** 2025 年 6 月，Canva 表示，现在希望后端、机器学习和前端岗位的候选人在一个新的“AI 辅助编程”(AI-Assisted Coding) 环节中使用 Copilot、Cursor 和 Claude 等 AI 工具。它评估候选人能否“拆解复杂、模糊的需求”“发现并修复 AI 生成代码中的问题”，以及“确保 AI 生成的方案达到生产标准”（[Canva Engineering，2025 年 6 月](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews)）。
- **试行 AI 辅助编程面试。** 2025 年 7 月，Business Today 援引 404 Media 报道称，Meta 正在打造一种候选人可以使用 AI 助手的编程面试，并引用 Meta 的说法：这“更能代表我们未来员工将要工作的开发环境，也会让基于大语言模型的作弊不那么有效”（[Business Today，2025 年 7 月](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31)）。
- **限制工具并改为线下面试。** 2025 年 3 月，CNBC 报道了一款帮助候选人在远程编程面试中悄悄使用 AI 的工具。在同一篇报道中，Amazon 表示候选人必须确认不会使用未经授权的工具，Google 的 CEO 建议招聘经理考虑安排一些线下面试，Deloitte 则已在其英国应届生项目中恢复了线下面试（[CNBC，经 NBC New York 转载，2025 年 3 月](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1)）。

这些只是几家大公司的做法，并非对市场的调查，而且政策也会变化。但它们指向同一个方向：远程的“从零写出这段代码”任务如今更难让人信任，真正值得关注的问题已经从“你能写出代码吗？”变成了“你对代码的理解是否足以判断它的好坏？”

## 为什么知识作为早期筛选更加重要

如果助手能写出代码初稿，那么优秀工程师和平庸工程师的区别在哪里？主要在于助手无法替他们提供的东西：

- **概念与原理。** 了解数据库如何使用索引、竞态条件为何发生、某个框架在每次请求时做了什么，工程师才能看出生成的代码哪里错了。
- **阅读代码。** 在使用 AI 的输出之前，必须有人读懂它，知道它会打印、返回或修改什么。
- **调试。** 当“几乎正确”的代码出错时，修复依赖于理解出错的原因。
- **判断力。** 在两种都能运行的方案之间做选择，需要了解各种权衡：性能、安全性、可维护性。

这些都是知识和推理能力，可以直接、快速地考察。招聘研究早已把岗位知识测试列为平均预测力较好的工作绩效预测方法之一：在 2022 年对数十年研究的重新分析中，Sackett、Zhang、Berry 和 Lievens 估计岗位知识测试的效度为 .40，接近结构化面试的 .42（[doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)）。这项研究早于 AI 助手出现，因此无法证明任何关于 AI 时代工作的结论。但它支持把针对岗位的知识测试用作早期筛选，而上文描述的转变让这种测试所考察的知识在工作中更加核心，而不是相反。

## 动手练习依然有一席之地

以上并不意味着编程练习没用了，而是改变了它们的安排时机和形式：

- **与 AI 结对。** 像 Canva 的环节那样，给候选人一个 AI 助手和一个贴近实际的开放式任务。观察他们如何拆解问题、向助手提什么问题，以及接受或拒绝哪些结果。
- **代码审查。** 交给候选人一个 pull request（也许由 AI 编写），里面有几个真实的 bug。问他们会改什么、为什么改。
- **调试。** 给出一个有测试失败的小型代码库。这与调查中描述的日常工作非常接近，也很难作假。
- **系统设计。** 对于高级岗位，围绕权衡取舍的讨论能体现判断力，这是任何一条提示词都给不出的。

这些练习的执行和评分都要占用工程师的时间。这正是要在它们之前安排一次快速、覆盖面广的知识检查的主要原因：让这些练习留给最有可能成功的候选人。

## 适合 AI 时代的招聘流程

1. **申请筛选只看硬性要求：** 工作许可、所在地、必备经验。
2. **进行一次简短的知识笔试，** 考察与你们技术栈相关的概念、原理和代码阅读。
3. **安排一次动手练习，** 形式要符合你们团队的工作方式：AI 辅助结对、代码审查或调试，远程或线下均可。
4. **为高级岗位增加系统设计。**
5. **进行一场结构化面试，** 使用固定问题和评分标准，其中包括候选人如何使用 AI 工具、如何检查其输出。
6. **由人做决定，** 每一项结果都只是参考之一。

提前告诉候选人每个阶段允许使用哪些工具。明确的规则比让人去猜更公平，也让结果更容易比较。

完整的分步版本请参阅[如何招聘工程师](/guides/hiring-engineers)。

## prepza 的定位

prepza 非常适合第 2 步。它会把你的职位描述变成一场限时选择题知识面试；在生成任何题目之前，你会先审核建议的主题，因此测试只覆盖你们的技术栈，不多也不少。

- **来自职位描述的概念与原理：** 数据库、API、架构、某个框架的行为、安全实践。
- **代码阅读题：** 给出一小段代码，问它会打印或返回什么、它做了什么、为什么出错，或者哪处修改能修复它。这正是 AI 辅助工作所依赖的审查能力。
- **每道题都有计时：** 每道题有自己的倒计时，由服务器强制执行，每位候选人拿到自己的一组随机题目。这会让查答案（包括询问 AI 助手）变得更难，但并非不可能。
- **诚信信号：** 评分卡会标记快到不可能读完题目的回答、候选人离开页面的次数以及尝试复制的情况。候选人完成后，报告还会指出把题目交给 AI、再照抄其答案时常留下的作答模式：无论题目长短或难易，每道题用时都差不多；或者难题答对，简单题却答错。标记或模式只是值得仔细查看的理由，不能证明作弊。
- **供真人面试追问的题目：** 报告会从候选人最擅长的主题中，推荐最多 3 道其答对的题目，供你在真人面试中深入讨论，在那里没有 AI 能替候选人作答。

prepza 不做的事：候选人不会在 prepza 中编写、运行或调试代码，prepza 也不会观察他们如何使用 AI 助手。这些属于动手练习阶段，可以在内部进行，也可以使用开发者测评平台，与知识笔试形成互补。可以从[按岗位分类的技能测试](/tests)中挑选现成的测试作为起点；关于 prepza 如何使用 AI、哪些事情留给人来做，请参阅 [AI 面试](/ai-interviews)。

## 公平性与候选人体验

调整流程正是检查它是否公平的好时机：

- **在每个阶段以书面形式明确 AI 使用规则。**
- **同一阶段对所有人保持相同条件。**
- **为提出需要的候选人提供合理便利，** 例如额外时间。
- **不要把信号当作结论。** 停顿、移开视线或答得很快都可能有无辜的原因。
- **保持简短。** 每多加一个阶段，都会占用优秀候选人的时间，而他们可能会把这些时间花在另一个 offer 上。

## 总结

AI 助手让写代码变得更便宜，也让判断代码变得更重要。好的流程应当体现这一点：在早期考察知识、原理和代码阅读，这样做既快，而且每道题都有计时，更难找人代答；然后再通过动手练习（通常允许使用 AI）来观察候选人如何工作。把规则讲清楚，并让人来掌握最终决定。

## 参考来源

- Stack Overflow, [2025 Developer Survey: AI](https://survey.stackoverflow.co/2025/ai).
- GitHub, [Octoverse 2025](https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/)，2025 年 10 月 28 日。
- Canva Engineering, [Yes, you can use AI in our interviews](https://canva.dev/blog/engineering/yes-you-can-use-ai-in-our-interviews)，2025 年 6 月 11 日。
- Business Today, [Meta to test job applicants with AI-assisted coding interviews](https://www.businesstoday.in/amp/technology/news/story/meta-to-test-job-applicants-with-ai-assisted-coding-interviews-amid-ai-expansion-plans-487200-2025-07-31)，2025 年 7 月 31 日，援引 404 Media。
- CNBC，经 NBC New York 转载, [Meet the 21-year-old helping coders use AI to cheat in Google and other tech job interviews](https://www.nbcnewyork.com/news/business/money-report/meet-the-21-year-old-helping-coders-use-ai-to-cheat-in-google-and-other-tech-job-interviews/6178911/?amp=1)，2025 年 3 月 9 日。
- Sackett, P. R., Zhang, C., Berry, C. M., & Lievens, F. (2022). Revisiting meta-analytic estimates of validity in personnel selection. *Journal of Applied Psychology, 107*, 2040–2068. [doi:10.1037/apl0000994](https://doi.org/10.1037/apl0000994)

## 延伸阅读

- [如何招聘工程师](/guides/hiring-engineers)
- [按岗位分类的技能测试](/tests)
- [在线测评中的作弊行为，以及真正有效的应对方法](/guides/cheating-in-online-assessments)
- [AI 面试：是什么，以及如何公平地使用](/ai-interviews)
- [技能测试与简历筛选对比](/guides/skills-tests-vs-cv-screening)
