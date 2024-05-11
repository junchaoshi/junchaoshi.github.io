---
layout: page
permalink: /publications/
title: Publications
description: "* indicates equal contributions, # indicates corresponding author.<h6>An up-to-date list is available on <a href='https://scholar.google.com/citations?user=v04jJXoAAAAJ&hl=en'>Google Scholar</a>.</h6>"
years: [2024, 2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012]
years_big: [2024, 2023]
years_ucr: [2023, 2022, 2021, 2020]
years_unr: [2019, 2018, 2017]
years_ioz: [2017, 2016, 2015, 2014, 2013, 2012]
nav: true
nav_order: 1
---
<!-- altmetric -->
<script type='text/javascript' src='https://d1bxh8uas1mnw7.cloudfront.net/assets/embed.js'></script>
<script async src="https://badge.dimensions.ai/badge.js" charset="utf-8"></script>

<!-- _pages/publications.md -->
<div class="publications">

<h6>
<a href="#works_at_BIG">🧑‍🏫Works at BIG</a>
<a href="#works_at_UCR">👨‍🎓Works at UCR</a>
<a href="#works_at_UNR">🧑Works at UNR</a>
<a href="#works_at_IOZ">👶Works at UCAS</a>
</h6>

<a name="works_at_BIG"></a>
<h1>Works at BIG</h1>

{%- for y in page.years_big %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_BIG -q @*[year={{y}}]* %}
{% endfor %}

<a name="works_at_UCR"></a>
<h1>Works at UCR</h1>

{%- for y in page.years_ucr %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_UCR -q @*[year={{y}}]* %}
{% endfor %}

<a name="works_at_UNR"></a>
<h1>Works at UNR</h1>

{%- for y in page.years_unr %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_UNR -q @*[year={{y}}]* %}
{% endfor %}

<a name="works_at_IOZ"></a>
<h1>Works at UCAS</h1>

{%- for y in page.years_ioz %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_IOZ -q @*[year={{y}}]* %}
{% endfor %}

</div>
