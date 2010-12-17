require 'polyglot'
require 'treetop'

#class Treetop::Runtime::SyntaxNode
#  def method_missing(m, *args, &block)
#    puts "There's no method called #{m} here for #{self.class}"
#  end
#end

require_relative 'nodes'
require_relative 'util'
require_relative 'runtime'

Treetop.load "declarative"
parser = DeclarativeParser.new
parser.consume_all_input = true


#root = parser.parse("def myfunk( ) { s1 s2 }", :root => :func_def)
#root = parser.parse(" { x = y = 1 + 2; f = def lambada() { sublocal1 = sublocal2; }; }", :root => :block)
src = <<SOURCE
x = y = 1 + 2;
def lambada() {
  sublocal1 = sublocal2;
};
SOURCE
root = parser.parse(src, :root => :statements)

if root
  puts "Node:   #{root}"
  puts "Parsed: #{root.text_value}"
  puts "Result: #{root.value}"
  puts "Tree:"
  print_tree(root.value)

  #context = EvaluationContext.new
  #root.value.eval(context)
else
  puts ""
  puts "Failure: #{parser.failure_reason}"
  puts "Location: #{parser.failure_line}:#{parser.failure_column}"
end