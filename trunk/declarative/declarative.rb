require 'polyglot'
require 'treetop'
require_relative 'nodes'
require_relative 'util'

Treetop.load "declarative"
parser = DeclarativeParser.new
parser.consume_all_input = true

#root = parser.parse("def myfunk( ) { s1 s2 }", :root => :func_def)
root = parser.parse("{ x = y = 1 + 2; }", :root => :block)

if root
  puts "Node:   #{root}"
  puts "Parsed: #{root.text_value}"
  puts "Result: #{root.value}"
  puts "Tree:"
  print_tree(root.value)
  root.value.eval("context")
else
  puts ""
  puts "Failure: #{parser.failure_reason}"
  puts "Location: #{parser.failure_line}:#{parser.failure_column}"
end