require_relative "nodes"

# Where root is a ParseNode
def print_tree(root, offset = 0)
  return if root == nil

  off = '  ' * offset
  if root.class.to_s == "Array"
    puts "#{off}[]"
  else
    puts "#{off}#{root}"
  end

  # Try to avoid situations where 'root' is not a ParseNode but Array/String/Fixnum
  children = if root.class == Array
               root
             elsif root.class == String
               []
             elsif root.class == Fixnum
               []
             elsif root.kind_of? ParseNode
               root.children
             else
               raise "unsupported node class #{root.class}"
             end
  children.map do |e|
    print_tree(e, offset+1)
  end
end

#def assert_eq(expected, actual)
#  if expected != actual
#    throw "assertion failed: #{expected} vs #{actual}"
#  end
#end