---
layout: page
permalink: /zh/research/
title: 研究方向
lang: zh-CN
translation_key: research
alternate_url: /research/
alternate_lang: en
---
<a id="toc"></a>

基因组学最重要的发现之一，是认识到哺乳动物基因组中仅有约 1–2% 的 DNA 能够编码蛋白质，而超过 90% 的基因组 DNA 会被转录为非蛋白编码 RNA。我们的实验室综合运用数学、生物信息学与生物学方法，解析由 `RNA 密码` 介导的复杂调控网络，并探索其在人类疾病诊断和治疗中的意义。

#### 当前研究方向

###### [非经典小 RNA](#sec-1) <br>
* [开发新型小 RNA 测序方法与分析工具](#sec-1-1) <br>
* [发现非经典小 RNA 及其功能](#sec-1-2) <br>

###### [哺乳动物胚胎对称性破缺](#sec-2) <br>
* [寻找驱动哺乳动物胚胎分裂与分化的力量](#sec-2-1) <br>

---

<a id="sec-1"></a>

#### **非经典小 RNA**
小 RNA 是一类从细菌到哺乳动物中广泛存在的非编码 RNA。miRNA、piRNA 等经典小 RNA 已得到多方面深入研究，但对 tRNA 来源小 RNA（`tsRNA`）、rRNA 来源小 RNA（`rsRNA`）等非经典小 RNA 的认识仍然有限。

<div class="row justify-content-md-center">
    <div class="col-sm mt-3 mt-md-0">
        {% include figure.html path="assets/img/research/sncRNAtools.jpg" title="探索小 RNA 世界" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption"><b>探索小 RNA 世界。</b>高通量 RNA 测序方法和注释工具是获取小 RNA 信息的必要手段。</div>

<a id="sec-1-1"></a>

##### **开发新型小 RNA 测序方法与分析工具**
为了探索不断扩展的小 RNA 世界，我们开发了小 RNA 分析工具 <a href="https://www.sciencedirect.com/science/article/pii/S1672022918300445" target=_blank>SPORTS</a>。该注释工具便于同时研究经典与非经典小 RNA，并推动发现了可用于肺部疾病诊断的 <a href="https://link.springer.com/article/10.1186/s12943-020-01280-9" target=_blank>TRY-RNA signature</a>。我们还开发了新型小 RNA 测序方法 <a href="https://www.nature.com/articles/s41556-021-00652-7" target=_blank>PANDORA-seq</a>，用于克服 RNA 修饰对传统 RNA-seq 检测小 RNA 的阻碍。该方法揭示了此前未知的小 RNA 图谱：在多种组织和细胞中，占主导地位的并非 miRNA，而是 tsRNA/rsRNA。

<div class="row">
    <div class="col-sm-8 mt-3 mt-md-0">
        {% include figure.html path="assets/img/research/SPORTSspecies.jpg" title="SPORTS 物种参考数据库" class="img-fluid rounded z-depth-1" %}
    </div>
    <div class="col-sm-4 mt-3 mt-md-0">
        {% include figure.html path="assets/img/research/PADNORASEQcompare.jpg" title="PANDORA-seq 与传统方法比较" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption"><b>左：</b>SPORTS1 预编译参考数据库。<b>右：</b>PANDORA-seq 相对于传统方法的优势。</div>

<a id="sec-1-2"></a>

##### **发现非经典小 RNA 及其功能**
十多年前，我们在<a href="https://www.nature.com/articles/cr2012141" target=_blank>小鼠成熟精子中发现了一类新的非经典小 RNA——tsRNA</a>，首次证明 tsRNA 在生理条件下存在。随后，我们发现 tsRNA 不仅存在于精子，也广泛存在于多种脊椎动物的<a href="https://academic.oup.com/jmcb/article/6/2/172/964660" target=_blank>血清</a>中，并对病理状态敏感。

越来越多的证据表明，父代暴露所获得的性状可被精子“记忆”并遗传给后代，因此我们进一步研究了<a href="https://www.science.org/doi/full/10.1126/science.aad7977" target=_blank>精子小 RNA 在表观遗传中的作用</a>。我们发现，父代高脂饮食会改变小鼠精子 tsRNA 的表达谱；富含 tsRNA/rsRNA 的 30–40 nt 精子 RNA 组分及其 RNA 修饰可作为父系表观遗传信息的载体。我们还发现 RNA 甲基转移酶 <a href="https://www.nature.com/articles/s41556-018-0087-2" target=_blank>Dnmt2</a> 能够塑造精子 `RNA 密码` 并影响性状遗传。

---
<a id="sec-2"></a>

#### **哺乳动物胚胎对称性破缺**
2005 年 7 月 1 日，《Science》列出了 125 个重要科学问题，其中一个问题尤其吸引我们：<a href="https://www.science.org/doi/10.1126/science.309.5731.78b" target=_blank>**胚胎中的不对称性是如何决定的？**</a><br>

在线虫、青蛙和海胆等物种中，后代卵裂球的命运由不对称分布的形态发生素决定；而哺乳动物胚胎的细胞命运指定更为精细，由卵裂球之间逐步形成的差异引导。哺乳动物产卵数量较少，胚胎可能因此需要更强的发育韧性以避免早期死亡。关于哺乳动物胚胎的发育可塑性仍存在争论：缺乏预先模式并不意味着卵裂球完全相同，细胞之间的细微差异可能逐渐放大，在保持发育可塑性的同时驱动模式形成。

<div class="row justify-content-md-center">
    <div class="col-sm-12 mt-3 mt-md-0">
        {% include figure.html path="assets/img/research/symmetrybreaking.jpg" title="胚胎对称性破缺" class="img-fluid rounded z-depth-1" %}
    </div>
</div>
<div class="caption"><b>对称性破缺模型。</b>胚胎发育过程中由单稳态向双稳态转变的过程。</div>

<a id="sec-2-1"></a>

##### **寻找驱动哺乳动物胚胎分裂与分化的力量**
哺乳动物着床前胚胎中的细胞，需要在有限次数的分裂中由全能状态转变为不同命运。卵裂球之间首次出现不对称性的时间，以及这种差异如何形成不同细胞命运，是长期存在的问题。通过<a href="https://journals.biologists.com/dev/article/142/20/3468/47006" target=_blank>单细胞 RNA 测序分析与数学建模</a>，我们发现最早的不对称性在第一次细胞分裂时便已出现，并呈二项分布。数学模型提示，细胞具有自然分化的倾向。我们的结果支持这样一种情形：早期卵裂球中相互竞争的谱系决定因子根据相对比例决定细胞命运，在出现形态差异前形成灵活的“谱系强度”。我们还揭示了异质表达的长非编码 RNA <a href="https://linkinghub.elsevier.com/retrieve/pii/S0092-8674(18)31564-2" target=_blank>LincGET</a> 在小鼠二细胞胚胎对称性破缺过程中的作用。
