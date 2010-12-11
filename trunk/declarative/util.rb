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

def assert_eq(expected, actual)
  if expected != actual
    throw "assertion failed: #{expected} vs #{actual}"
  end
end