require 'citrus'
Citrus.load 'addition'

class Function
  def initialize(id, arglist, block)
    @id = id
    @arglist = arglist
    @block = block

    puts "arglist = #{arglist}"
  end
  def to_s()
    return "def #{@id} #{@arglist} {...}"
  end
end

#input = File.new("1.my", "r").read()
input = <<EOF
def foo(x, x) {}

EOF

sum = Addition.parse(input)
puts "Parsed: #{sum.value}."
