require 'zlib'
require 'open-uri'
require 'rexml/document'
require 'iconv'

def download_release_xml(release_id, into)
  api_key = "f3934f44fc"
  url = "http://www.discogs.com/release/#{release_id}?f=xml&api_key=#{api_key}"
  headers = {'Accept-Encoding' => 'gzip', 'User-Agent' => 'MyDiscogsClient/1.0 +http://mydiscogsclient.org'}

  begin
    response = open(url, headers)
    begin
      data = Zlib::GzipReader.new(response)
    rescue Zlib::GzipFile::Error
      response.seek(0)
      data = response.read
    end
    File.open(into, 'w') { |f|
      f.write(data)
    }
  rescue OpenURI::HTTPError => e
    raise RuntimeError(e.io.read)
  end
end

def hms2sec(hms)
  if hms == ''
    0
  elsif hms =~ /(\d+):(\d+)/
    $1.to_i * 60 + $2.to_i
  else
    raise ArgumentError, "cannot parse duration '#{hms}'"
  end
end

def sec2hms(sec)
  mm = sec / 60
  ss = sec % 60
  sprintf("%d:%02d", mm, ss)
end

def handle_release_xml(xml_fname)
  File.open(xml_fname, "r") {|f|
    data = f.read()
    #puts "data: #{data}"
    doc = REXML::Document.new(data)
    #doc.elements.each("resp/release/tracklist/track") {|elem|
    #  pos = elem.get_elements("position")[0].get_text
    #  title = elem.get_elements("title")[0].get_text
    #  puts "#{title}"
    #}
    #puts "###"
    dur_sum = 0
    tracks = 0
    doc.elements.each("resp/release/tracklist/track") {|elem|
      pos = elem.get_elements("position")[0].get_text.to_s
      title = elem.get_elements("title")[0].get_text.to_s
      dur_str = elem.get_elements("duration")[0].get_text.to_s
      dur_sec = hms2sec(dur_str)
      dur_sum += dur_sec
      tracks += 1
      if dur_sec > 0
        puts "#{pos}. #{title} (#{dur_str})"
      else
        puts "#{pos}. #{title}"
      end
    }
    print "There are #{tracks} tracks lasting #{sec2hms(dur_sum)}\n"
  }
end

def parse_release_id(input)
  if input =~ /^\d+$/
    input.to_i
  elsif input =~ /discogs\.com\/.+\/release\/(\d+)/
    $1
  else
    raise ArgumentError, 'cannot parse release id #{input}'
  end
end

#release_id = 1688559
release_id = parse_release_id(ARGV[0])
#print "release_id: #{release_id}"
download_release_xml(release_id, "parse-discogs.tmp.xml")
handle_release_xml("parse-discogs.tmp.xml")