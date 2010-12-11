require 'polyglot'
require 'treetop'

class FuncDef
  def initialize(id, arglist, block)
    @id = id
    @arglist = arglist
    @block = block
  end
  def to_s()
    "#{self.class}(id=#{@id} args=#{@arglist} block=#{@block})"
  end
  def get_children
    [ @arglist, @block ]
  end
end

class Block
  def initialize(elements)
    @elements = elements
  end
  def to_s
    "#{self.class}"
  end
  def get_children
    @elements
  end
end

class Assignment
  def initialize(elements)
    @elements = elements
  end
  def to_s
    "#{self.class}(#{@elements.join(',')})"
  end
  def get_children; [ @elements ]; end
end

class Addition
  def initialize(elements)
    @elements = elements
  end
  def to_s
    "#{self.class}(#{@elements.join('+')})"
  end
  def get_children
    [ @elements ]
  end
end

class IdUse
  def initialize(id)
    @id = id
  end
  def to_s
    "'#{@id}'"
  end
  def get_children; []; end
end

Treetop.load "declarative"
#Treetop.load "arithmetic"

#puts "input: _#{input}_"

parser = DeclarativeParser.new
#parser = ArithmeticParser.new
parser.consume_all_input = true

#root = parser.parse("def myfunk( ) { s1 s2 }", :root => :func_def)
root = parser.parse("{ x = y = 1 + 2; }", :root => :block)

def print_tree(root, offset = 0)
  if root.class.to_s != "Array"
    off = ' ' * offset
    puts "#{off}#{root}"
  end
  chn = if root.class.to_s == "Array"
           root
         elsif root.class.to_s == "String"
           []
         else
           root.get_children
         end
  chn.map do |e|
    print_tree(e, offset+1)
  end
end

if root
  puts "Node:   #{root}"
  puts "Parsed: #{root.text_value}"
  puts "Result: #{root.value}"
  puts "Tree:"
  print_tree(root.value)
else
  puts ""
  puts "Failure: #{parser.failure_reason}"
  puts "Location: #{parser.failure_line}:#{parser.failure_column}"
end