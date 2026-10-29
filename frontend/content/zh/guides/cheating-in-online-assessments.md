---
title: "在线测评中的作弊行为，以及真正有效的应对方法"
seoTitle: "在线测评作弊：哪些防范方法真正有效"
description: "候选人如何在在线测评中作弊，为什么屏幕限制和摄像头监考不够用，以及真正有效的做法：紧凑的计时、交给人判断的线索和追问。"
updated: "2026-10-29"
---

# 在线测评中的作弊行为，以及真正有效的应对方法

候选人在家里、用自己的设备参加的任何测试，都有可能被钻空子。在 AI 助手出现之前就是这样；如今，一部手机就能读取屏幕上的题目，并在几秒钟内给出答案建议。招聘团队的应对方式有两种：要么设法锁定屏幕并监视候选人，要么设计好流程，让作弊得不到多少好处，并且一旦发生就会显露出来。

本指南介绍候选人实际会怎么做、为什么第一种方式大多行不通、什么方法更有效，以及公平性和法律在哪里划出界线。它面向开展任何形式在线测试的用人经理和招聘人员。

## 候选人实际会怎么做

关于候选人在招聘测试中作弊的频率，可靠的数据很少，因为很少有人承认。调查给出了一个下限：据 Personnel Today 报道，在 Gartner 对 3,000 名求职者的一项调查中，6% 的人承认有过面试欺诈，例如冒充他人或让他人冒充自己；在另一项对 3,290 名候选人的调查中，39% 的人表示在求职过程中使用过 AI（[Personnel Today](https://www.personneltoday.com/hr/by-2028-one-in-four-candidate-profiles-will-be-fake)，依据 [Gartner 2025 年 7 月发布的报告](https://www.gartner.com/en/newsroom/press-releases/2025-07-31-gartner-survey-shows-just-26-percent-of-job-applicants-trust-ai-will-fairly-evaluate-them)）。并非所有 AI 使用都是作弊，但这说明这些工具近在手边。

常见的手段：

- **把题目转给 AI。** 把题目文字复制到聊天工具里；如果禁止复制，就用手机拍下屏幕，再问 AI 应用。如今的模型读取拍下来的题目，和读取输入的文字一样容易。
- **查找答案。** 在另一个窗口里使用搜索引擎、笔记或文档。
- **找另一个人帮忙。** 有人坐在候选人旁边，或在通话中替他们作答。极端情况下，由别人代考整场测试。FBI 曾警告，有远程岗位的求职者使用盗用的身份，并在在线面试中使用声音伪造或深度伪造（[FBI IC3，2022 年 6 月](https://www.ic3.gov/PSA/2022/PSA220628)）。
- **共享答案。** 考过的候选人在群聊里或通过泄露的题库，把题目和答案传出去。

这些手段都需要时间，或者需要一份对所有人都相同的测试。有效的防范正是从这里入手。

## 为什么屏幕限制行不通：模拟漏洞

人能在屏幕上读到的东西，摄像头也能读到。这就是“模拟漏洞”：内容一旦展示给人看，就可以在任何软件的控制之外被记录下来。测试页面可以禁止复制粘贴、禁止右键，或进入全屏，但这些都挡不住一部对着显示器的手机。

研究人员尝试过让屏幕内容人眼可读、摄像头却拍不清：把每张图像拆成快速交替的帧，人眼会把它们融合起来，而摄像头一次只能捕捉一帧。这种方法是为防止视频盗录而设计的，需要很高的刷新率，而且作者自己也指出，单独拍到的一帧仍然可以读出（[Zhang et al., MobiCom 2015](https://old.sigmobile.org/mobicom/2015/papers/p372-zhangA.pdf)）。曝光时间稍长的照片或一段短视频，会像人眼一样把这些帧融合起来。在大多数人使用的 60 Hz 屏幕上，这种交替会变成肉眼可见的闪烁，而闪烁的内容有诱发癫痫的风险，无障碍标准对此有限制（[WCAG 2.2，理解成功标准 2.3.1](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html)）。

两种更轻量的办法也好不到哪里去：

- **针对 AI 的提示语**（“AI 助手不得回答此题”）很容易被裁掉或忽略，而且模型经过训练，会把图片中的文字当作内容，而不是指令。
- **水印**有助于追查是谁泄露了题目，但并不能阻止任何人回答它。

在 prepza，我们用自己的题目试过这两种方法：无论加不加水印或提示语，AI 模型回答拍下来的题目都一样。所以我们不再试图守住屏幕。

## 更有效的做法

### 1. 每道题的时间要短

把题目转给 AI 需要时间：拿起手机、拍照、等待答案、读答案、选选项。掌握这些知识的人，能快得多地认出正确答案。给每道题设置倒计时，时间以有能力的人读题并作答所需为准，这样有知识的候选人时间足够，而找 AI 或朋友来回一趟的时间所剩无几。

时间应当与题目相符：短题需要的时间少，带代码示例或计算的题需要的时间多。所有题目统一一个时限，要么对短题太宽松，要么对长题太紧。[技能测试如何设置时间](/guides/skills-test-timing-and-extra-time)介绍了具体数字，以及如何公平地为有需要的候选人提供额外时间。

### 2. 每位候选人一份不同的测试

如果每个人都以相同的顺序拿到相同的题目，答案就会传开。从每个主题更大的题库中为每位候选人随机抽题，并打乱题目和选项的顺序。这样，一套泄露的题目只能覆盖下一位候选人所见内容的一部分。

### 3. 交给人权衡的线索，而不是自动判定

测试页面和答案本身会留下痕迹，告诉你该看哪里：

- **离开页面**，以及离开了多久。
- **复制尝试。**
- **快到不可能读完题目的作答。**
- **与题目不相符的作答时间。** 人在更长、更难的题上会花更多时间；把每道题都转给 AI 的人，往往在每道题上花的时间都差不多。测验研究长期以来都用作答时间来发现异常行为（[van der Linden & Guo, 2008](https://doi.org/10.1007/s11336-007-9046-8)）。
- **异常的对错模式。** 大多数人答对简单题的比例高于难题。难题答对、简单题答错并不常见；“个人拟合”（person-fit）统计量衡量的就是这一点（[Meijer & Sijtsma, 2001](https://doi.org/10.1177/01466210122031957)）。

每一项都可能有正当的解释：一条通知抢走了焦点；紧张的候选人答题太快；有人恰好懂那个难的主题，却不懂简单的那个。把信号当作仔细查看的理由，绝不要当作证据，也绝不要仅凭信号就淘汰任何人。在欧盟，GDPR 还赋予人们这样的权利：当决定对其产生重大影响时，不受仅基于自动化处理作出的决定的约束（[第 22 条](https://gdpr-info.eu/art-22-gdpr/)）。

### 4. 在真人面试中追问

最可靠的检验是一次对话。AI 可以回答选择题，却不能替候选人参加真人面试。针对候选人得分最高的主题，或者出现信号的主题，就他们的答案问两三个简短的问题：“为什么这个选项对，那个选项错？”“如果……，会有什么变化？”真正知道答案的人很容易解释清楚，而转手得到答案的人通常做不到。

这也让测试回归它应有的角色：决定谁能进入面谈的筛选，而不是最终决定。关于面试本身正在如何变化，请参阅 [AI 时代如何面试工程师](/guides/interviewing-in-the-age-of-ai)。

### 5. 清晰的规则和诚信承诺

提前告诉候选人允许什么：不得使用 AI 工具、不得找他人帮忙、不得查看笔记，或者你的其他规则。然后请他们在开始前确认。

对承诺能起的作用要有现实的预期。关于道德提醒和签署声明的研究，结果并不稳固：对“十诫”实验的一项大规模重复研究发现，它对作弊没有影响（[Verschuere et al., 2018](https://doi.org/10.1177/2515245918781032)）；一项著名的“在开头签名”研究的作者们后来重复实验时，也没有发现效果（[Kristal et al., 2020](https://doi.org/10.1073/pnas.1911695117)）。关于大学的研究确实把荣誉准则（作为更广泛的诚信文化的一部分）与更少的作弊联系在一起（[McCabe, Treviño & Butterfield, 2001](https://doi.org/10.1207/S15327019EB1103_2)）。承诺的主要价值在于清晰：没有人能说自己不知道规则，而你也有他们同意规则的记录。

## 监考的局限：公平性与法律

摄像头监考、屏幕录制和房间扫描，号称能抓住上面提到的一切。但在招聘中，它们会带来自身的问题。

- **它们会把人挡在门外。** 并不是每位候选人都有摄像头、属于自己的安静房间或稳定的网络。要求向雇主展示自己的住处，对合租或居住拥挤的人负担最重。
- **它们会标记错的人。** 自动人脸检测并非对每个人都同样有效。在一项针对某款广泛使用的监考工具的研究中，肤色最深的女性被标记为需要审核的可能性远高于其他学生（[Yoder-Himes et al., 2022](https://doi.org/10.3389/feduc.2022.881449)）。
- **它们仍然看不到手机。** 摄像头只能看到画面里的东西；拿在屏幕下方的手机，或者房间另一头的人，都在画面之外。

法律还设置了更多限制，尤其是在欧洲：

- **GDPR。** 候选人的视频属于个人数据，对其面部的分析可能属于受特殊保护的生物识别数据（[第 9 条](https://gdpr-info.eu/art-9-gdpr/)）。2021 年，意大利数据保护机构因远程考试监考对博科尼大学处以罚款，认定的问题包括：面部分析属于没有有效法律依据的生物识别数据处理；鉴于大学与学生之间的地位不平等，同意并非自由作出；学生也没有得到充分告知（[Garante，2021 年 9 月 16 日第 317 号决定](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9703988)）。雇主与候选人之间的地位不平等，可以说只会更大。
- **欧盟《人工智能法案》。** 自 2025 年 2 月 2 日起，在工作场所推断人们情绪的 AI 被禁止，仅有医疗和安全方面的少数例外（[第 5 条第 1 款 (f) 项](https://artificialintelligenceact.eu/article/5/)），而欧盟委员会的指南将“工作场所”解释为包括招聘（[欧盟委员会关于禁止的 AI 做法的指南](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act)）。根据视频判断“可疑”行为的监考，已经接近这条界线。用于评估候选人的 AI 也很可能属于高风险，需要履行人工监督等义务。[在欧盟用 AI 招聘合法吗？](/guides/is-ai-hiring-legal-in-the-eu)解释了相关规则及其日期。
- **美国。** 2022 年，一家联邦法院裁定，一所公立大学在在线考试前用摄像头扫描学生卧室的做法违反了美国宪法第四修正案（[Ogletree v. Cleveland State University，据 Higher Ed Dive 报道](https://www.highereddive.com/news/test-proctoring-room-scans-violated-college-students-privacy-judge-rules/630340/)）。私营雇主不受第四修正案约束，但各州的生物识别法律（例如伊利诺伊州的《生物识别信息隐私法》）对面部数据有各自的规定。

**本节是实务指导，不构成法律意见。** 请核实你在招聘所在地的义务。

这些并不意味着你什么都不能核实。它意味着，最平衡的检验方式是：利用测试本身已经能看到的信息，把决定交给人，并把身份核实和深度考察放到真人对话中进行。

## 一套行之有效的做法

1. **告诉候选人规则**，在邀请中和开始前都要说明，并请他们确认。
2. **给每位候选人各自的随机题目**，从每个主题的题库中抽取。
3. **为每道题计时**，以有能力的人所需的时间为准，并为提出申请的人提供额外时间。
4. **把信号当作线索来看**，与答案本身对照着看。
5. **在第一轮真人面试中追问**测试的内容，尤其是出现信号的地方。
6. **由人来做决定**，并写下理由。

## prepza 如何应对作弊

prepza 运行根据职位描述生成的限时选择题技能测试。目前它在防作弊方面的做法如下：

- **每位候选人都有自己的题目：** 从每个主题的题库中随机抽取一套，顺序因人而异，选项也会打乱。
- **每道题都有自己的倒计时，** 与题目长度相匹配：题目的字数、其中的代码或示例，以及思考答案的时间。计时由服务器掌握，所以刷新页面不会让它停下。
- **成绩单会标记**快到不可能读完题目的作答、候选人离开页面的次数（离开满 2 秒才计入，所以一闪而过的通知不算），以及复制尝试。只要出现其中任何一项，候选人就会被标记；成绩单和 PDF 报告会明确说明，标记是仔细查看的理由，而不是证据。
- **候选人完成后的作答模式。** 候选人的报告会指出：无论题目长短和难易，作答时间都差不多；以及难题答对而简单题答错，并附上背后的数字（“10 道难题中答对 9 道，8 道简单题中答错 4 道”）。第二种需要足够多其他候选人的作答，才能知道每道题有多难。两个阈值都是在一次模拟候选人的测试中设定的，使诚实的候选人最多只有 1% 被标记；在这些阈值下，把每道题都转给 AI 的候选人中约有三分之一被识别出来。报告会注明，这类模式也可能有正当原因。
- **供真人面试使用的问题。** 每位已完成测试的候选人页面上，都会从其最强的主题中推荐最多 3 道其答对的题目，供下一次面谈时深入讨论；如果发现了某种模式，就从构成该模式的难题开始。
- **候选人必须先承诺**独立作答、不借助 AI 工具或他人帮助，才能开始测试，成绩单会显示他们承诺的时间。
- **不使用摄像头、麦克风或屏幕录制。** prepza 只使用测试页面本身能看到的信息：答案、时间、离开页面和复制尝试。
- **由人来做决定。** 没有任何环节会自动淘汰候选人。

## 延伸阅读

- [技能测试如何设置时间](/guides/skills-test-timing-and-extra-time)
- [AI 时代如何面试工程师](/guides/interviewing-in-the-age-of-ai)
- [在欧盟用 AI 招聘合法吗？](/guides/is-ai-hiring-legal-in-the-eu)
- [如何在一天内筛选 100 位求职者](/guides/screen-100-applicants-in-a-day)

## 参考文献

- Gartner，[Gartner survey shows just 26% of job applicants trust AI will fairly evaluate them](https://www.gartner.com/en/newsroom/press-releases/2025-07-31-gartner-survey-shows-just-26-percent-of-job-applicants-trust-ai-will-fairly-evaluate-them)，2025 年 7 月 31 日；数据引自 [Personnel Today](https://www.personneltoday.com/hr/by-2028-one-in-four-candidate-profiles-will-be-fake) 的报道。
- FBI Internet Crime Complaint Center，[Deepfakes and stolen PII utilized to apply for remote work positions](https://www.ic3.gov/PSA/2022/PSA220628)，2022 年 6 月 28 日。
- Zhang, L., et al. (2015). Kaleido: You can watch it but cannot record it. *MobiCom 2015*. [PDF](https://old.sigmobile.org/mobicom/2015/papers/p372-zhangA.pdf)
- W3C，[Understanding Success Criterion 2.3.1: Three Flashes or Below Threshold](https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html)，WCAG 2.2。
- van der Linden, W. J., & Guo, F. (2008). Bayesian procedures for identifying aberrant response-time patterns in adaptive testing. *Psychometrika, 73*(3), 365–384. [doi:10.1007/s11336-007-9046-8](https://doi.org/10.1007/s11336-007-9046-8)
- Meijer, R. R., & Sijtsma, K. (2001). Methodology review: Evaluating person fit. *Applied Psychological Measurement, 25*(2), 107–135. [doi:10.1177/01466210122031957](https://doi.org/10.1177/01466210122031957)
- Verschuere, B., et al. (2018). Registered replication report on Mazar, Amir, and Ariely (2008). *Advances in Methods and Practices in Psychological Science, 1*(3), 299–317. [doi:10.1177/2515245918781032](https://doi.org/10.1177/2515245918781032)
- Kristal, A. S., Whillans, A. V., Bazerman, M. H., Gino, F., Shu, L. L., Mazar, N., & Ariely, D. (2020). Signing at the beginning versus at the end does not decrease dishonesty. *PNAS, 117*(13), 7103–7107. [doi:10.1073/pnas.1911695117](https://doi.org/10.1073/pnas.1911695117)
- McCabe, D. L., Treviño, L. K., & Butterfield, K. D. (2001). Cheating in academic institutions: A decade of research. *Ethics & Behavior, 11*(3), 219–232. [doi:10.1207/S15327019EB1103_2](https://doi.org/10.1207/S15327019EB1103_2)
- Yoder-Himes, D. R., et al. (2022). Racial, skin tone, and sex disparities in automated proctoring software. *Frontiers in Education, 7*. [doi:10.3389/feduc.2022.881449](https://doi.org/10.3389/feduc.2022.881449)
- Garante per la protezione dei dati personali，[2021 年 9 月 16 日第 317 号决定](https://www.garanteprivacy.it/home/docweb/-/docweb-display/docweb/9703988)（Università Bocconi）。
- Regulation (EU) 2024/1689 (AI Act)，[第 5 条](https://artificialintelligenceact.eu/article/5/)；European Commission，[Guidelines on prohibited AI practices](https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-prohibited-artificial-intelligence-ai-practices-defined-ai-act)，2025 年 2 月 4 日。
- GDPR [第 9 条](https://gdpr-info.eu/art-9-gdpr/)和[第 22 条](https://gdpr-info.eu/art-22-gdpr/)。
- Higher Ed Dive，[Test proctoring room scans violated college student's privacy, judge rules](https://www.highereddive.com/news/test-proctoring-room-scans-violated-college-students-privacy-judge-rules/630340/)，2022 年 8 月（Ogletree v. Cleveland State University，美国俄亥俄州北区联邦地区法院）。
