module Jekyll
  module BibliographyYears
    def bibliography_years(input)
      site = @context.registers[:site]
      scholar = site.config['scholar'] || {}
      source_dir = scholar.fetch('source', '_bibliography').to_s.sub(%r{\A/+}, '')
      filename = input.to_s
      filename = "#{filename}.bib" unless filename.end_with?('.bib')
      path = File.join(site.source, source_dir, filename)

      return [] unless File.file?(path)

      contents = File.read(path).encode('UTF-8', invalid: :replace, undef: :replace)
      contents.scan(/^\s*year\s*=\s*[{"]?\s*(\d{4})/i).flatten.map(&:to_i).uniq.sort.reverse
    end
  end
end

Liquid::Template.register_filter(Jekyll::BibliographyYears)
