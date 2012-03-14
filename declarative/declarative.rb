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

src = <<SOURCE
x = y = 11;
SOURCE
root = parser.parse(src, :root => :source_unit)

if root
  puts "Node:   #{root}"
  puts "Parsed: #{root.text_value}"
  puts "Result: #{root.value}"
  puts "Tree:"
  print_tree(root.value)

  context = EvaluationContext.new()
  root.value.eval(context)
else
  puts ""
  puts "Failure: #{parser.failure_reason}"
  puts "Location: #{parser.failure_line}:#{parser.failure_column}"
end