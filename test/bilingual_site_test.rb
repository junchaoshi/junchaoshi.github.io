site = File.expand_path('../_site', __dir__)

def assert(condition, message)
  raise message unless condition
end

%w[index research team publications repositories contact news cv].each do |page|
  english = page == 'index' ? 'index.html' : "#{page}/index.html"
  chinese = page == 'index' ? 'zh/index.html' : "zh/#{page}/index.html"
  assert File.file?(File.join(site, english)), "missing #{english}"
  assert File.file?(File.join(site, chinese)), "missing #{chinese}"
end

home = File.read(File.join(site, 'zh/index.html'), encoding: 'UTF-8')
assert home.include?('<html lang="zh-CN">'), 'Chinese lang attribute is missing'
assert home.include?('hreflang="en"'), 'English alternate link is missing'
assert home.include?('>工具</a>'), 'Chinese navigation must use 工具'
assert !home.include?('>软件</a>'), 'Chinese navigation must not use 软件'

members = Dir.glob(File.join(site, 'zh/members/*/index.html'))
assert members.length == 12, "expected 12 Chinese member pages, found #{members.length}"

xiang = File.read(File.join(site, 'members/XiangLi/index.html'), encoding: 'UTF-8')
assert xiang.include?('Xiang Li'), 'English profile must display Xiang Li'

puts 'Bilingual site checks passed.'
