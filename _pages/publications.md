---
layout: page
permalink: /publications/
title: Publications
description: "* indicates equal contributions, # indicates corresponding author.<h6>An up-to-date list is available on <a href='https://scholar.google.com/citations?user=v04jJXoAAAAJ&hl=en'>Google Scholar</a>.</h6>"
nav: true
nav_order: 1
---
<!-- altmetric -->
<script type='text/javascript' src='https://d1bxh8uas1mnw7.cloudfront.net/assets/embed.js'></script>
<script async src="https://integration-badge.dimensions.ai/static/ai/badge.js" charset="utf-8"></script>

<!-- _pages/publications.md -->
<div class="publications">

<h6>
<a href="#works_at_CNCB">🧑‍🏫Works at CNCB</a>
<a href="#works_at_UCR">👨‍🎓Works at UCR</a>
<a href="#works_at_UNR">🧑Works at UNR</a>
<a href="#works_at_IOZ">👶Works at UCAS</a>
</h6>

<a name="works_at_CNCB"></a>
<h1>Works at CNCB</h1>

{% assign years_cncb = "works_at_CNCB" | bibliography_years %}
{%- for y in years_cncb %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_CNCB -q @*[year={{y}}]* %}
{% endfor %}

<a name="works_at_UCR"></a>
<h1>Works at UCR</h1>

{% assign years_ucr = "works_at_UCR" | bibliography_years %}
{%- for y in years_ucr %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_UCR -q @*[year={{y}}]* %}
{% endfor %}

<a name="works_at_UNR"></a>
<h1>Works at UNR</h1>

{% assign years_unr = "works_at_UNR" | bibliography_years %}
{%- for y in years_unr %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_UNR -q @*[year={{y}}]* %}
{% endfor %}

<a name="works_at_IOZ"></a>
<h1>Works at UCAS</h1>

{% assign years_ioz = "works_at_IOZ" | bibliography_years %}
{%- for y in years_ioz %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_IOZ -q @*[year={{y}}]* %}
{% endfor %}

</div>
