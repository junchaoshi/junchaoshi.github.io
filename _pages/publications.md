---
layout: page
permalink: /publications/
title: Publications
description: "* indicates equal contributions, # indicates corresponding author.<h6>An up-to-date list is available on <a href='https://scholar.google.com/citations?user=v04jJXoAAAAJ&hl=en'>Google Scholar</a>.</h6>"
nav: true
nav_order: 1
---
<!-- _pages/publications.md -->
<div class="publications">

<h6>
<a href="#works_at_CNCB">🧑‍🏫Works at CNCB</a>
<a href="#works_at_UCR">👨‍🎓Works at UCR</a>
<a href="#works_at_UNR">🧑Works at UNR</a>
<a href="#works_at_IOZ">👶Works at UCAS</a>
</h6>

<div class="publication-filter">
  <input id="publication-filter-input" class="publication-filter-input" type="search" placeholder="Type to filter" aria-label="Filter publications">
</div>

<section class="publication-section">
<a name="works_at_CNCB"></a>
<h1>Works at CNCB</h1>

{% assign years_cncb = "works_at_CNCB" | bibliography_years %}
{%- for y in years_cncb %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_CNCB -q @*[year={{y}}]* %}
{% endfor %}
</section>

<section class="publication-section">
<a name="works_at_UCR"></a>
<h1>Works at UCR</h1>

{% assign years_ucr = "works_at_UCR" | bibliography_years %}
{%- for y in years_ucr %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_UCR -q @*[year={{y}}]* %}
{% endfor %}
</section>

<section class="publication-section">
<a name="works_at_UNR"></a>
<h1>Works at UNR</h1>

{% assign years_unr = "works_at_UNR" | bibliography_years %}
{%- for y in years_unr %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_UNR -q @*[year={{y}}]* %}
{% endfor %}
</section>

<section class="publication-section">
<a name="works_at_IOZ"></a>
<h1>Works at UCAS</h1>

{% assign years_ioz = "works_at_IOZ" | bibliography_years %}
{%- for y in years_ioz %}
  <h2 class="year">{{y}}</h2>
  {% bibliography -f works_at_IOZ -q @*[year={{y}}]* %}
{% endfor %}
</section>

<p id="publication-filter-empty" class="publication-filter-empty" hidden>No publications found.</p>

</div>

<script>
  document.addEventListener("DOMContentLoaded", function () {
    var input = document.getElementById("publication-filter-input");
    var empty = document.getElementById("publication-filter-empty");
    var sections = Array.from(document.querySelectorAll(".publication-section"));
    if (!input || !sections.length) return;

    function filterPublications() {
      var query = input.value.trim().toLowerCase();
      var totalVisible = 0;

      sections.forEach(function (section) {
        var sectionVisible = 0;
        var yearHeadings = Array.from(section.querySelectorAll("h2.year"));

        yearHeadings.forEach(function (heading) {
          var bibliography = heading.nextElementSibling;
          while (bibliography && !bibliography.matches("ol.bibliography")) {
            bibliography = bibliography.nextElementSibling;
          }
          if (!bibliography) return;

          var visibleInYear = 0;
          Array.from(bibliography.querySelectorAll(":scope > li")).forEach(function (item) {
            var matches = !query || item.textContent.toLowerCase().indexOf(query) !== -1;
            item.hidden = !matches;
            if (matches) visibleInYear += 1;
          });

          heading.hidden = visibleInYear === 0;
          bibliography.hidden = visibleInYear === 0;
          sectionVisible += visibleInYear;
        });

        section.hidden = sectionVisible === 0;
        totalVisible += sectionVisible;
      });

      if (empty) empty.hidden = totalVisible !== 0;
    }

    input.addEventListener("input", filterPublications);
  });
</script>
