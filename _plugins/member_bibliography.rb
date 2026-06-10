require 'jekyll/scholar/tags/bibliography'

module Jekyll
  class Scholar
    class MemberBibliographyTag < BibliographyTag
      def render(context)
        set_context_to context
        update_dependency_tree

        author = context.registers[:page]['publication_author'].to_s.strip
        return '' if author.empty?

        wanted_authors = author.split(/\s*;\s*/).map { |name| normalize_author_name(name) }
        @member_publication_authors = wanted_authors
        items = entries.select { |entry| entry_has_author?(entry, wanted_authors) }
        items = items[offset..max] if limit_entries?
        return '' if items.empty?

        "<h2 id=\"publications\">Publications</h2>\n" \
          "<div class=\"publications\">\n#{render_items(items)}\n</div>"
      end

      private

      def bibliography_tag(entry, index)
        return missing_reference unless entry

        liquid_template.render(
          reference_data(entry, index)
          .merge(site.site_payload)
          .merge({
            'index' => index,
            'page' => context.registers[:page],
            'details' => details_link_for(entry),
            'member_publication_authors' => @member_publication_authors
          }),
          {
            :registers => context.registers,
            :filters => [Jekyll::Filters]
          }
        )
      end

      def entry_has_author?(entry, wanted_authors)
        return false unless entry.author.respond_to?(:any?)

        entry.author.any? do |author|
          wanted_authors.include? normalize_parsed_author(author)
        end
      end

      def normalize_parsed_author(author)
        normalize_author_name("#{author.last}, #{author.first}")
      end

      def normalize_author_name(author)
        author.to_s.gsub(/\s+/, ' ').strip.downcase
      end
    end
  end
end

Liquid::Template.register_tag('member_bibliography', Jekyll::Scholar::MemberBibliographyTag)
