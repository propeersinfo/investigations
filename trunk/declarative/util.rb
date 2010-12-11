# Where root is a ParseNode
def print_tree(root, offset = 0)
  off = '  ' * offset
  if root.class.to_s == "Array"
    puts "#{off}[]"
  else
    puts "#{off}#{root}"
  end

  # Try to avoid situations where 'root' is not a ParseNode but Array/String/Fixnum
  chn = if root.class.to_s == "Array"
           root
         elsif root.class.to_s == "String"
           []
         elsif root.class.to_s == "Fixnum"
           []
         else
           root.get_children
         end
  chn.map do |e|
    print_tree(e, offset+1)
  end
end

#def assert_eq(expected, actual)
#  if expected != actual
#    throw "assertion failed: #{expected} vs #{actual}"
#  end
#end