# Parse tree nodes.
# Once built such a tree could be evaluated.

class Node
  def eval(context)
    raise "eval is not implemented for class #{self.class}"
  end
end

###################################

class FuncDef < Node
  def initialize(id, arglist, block)
    @id = id
    @arglist = arglist
    @block = block
  end
  def to_s(); "#{self.class}(id=#{@id} args=#{@arglist} block=#{@block})"; end
  def get_children; [ @arglist, @block ]; end
end

###################################

class Block < Node
  def initialize(elements)
    @elements = elements
  end

  def to_s; "#{self.class}"; end

  def get_children; @elements; end

  def eval(context)
    @elements.map do |e|
      e.eval(context)
    end
  end
end

###################################

# Represents expressions like 'a = b = c' or just 'a'
class Assignment < Node
  def initialize(elements)
    raise "At least one element expected" unless (elements.size > 0)
    @elements = elements
  end

  def to_s; "#{self.class}[#{@elements.size}]"; end

  def get_children; [ @elements ]; end

  def eval(context)
    # evaluate the most right element
    rvalue = @elements.last.eval(context)
    # assign tat value to all the preceding elements
    @elements.reverse[1..-1].each do |e|
      puts "perform assignment: #{e} = #{rvalue}"
    end
  end
end

###################################

class Addition < Node
  def initialize(elements)
    @elements = elements
  end

  def to_s; "#{self.class}[#{@elements.size}]"; end

  def get_children; [ @elements ]; end

  def eval(context)

  end
end

###################################

class IdUse < Node
  def initialize(id)
    @id = id
  end
  def to_s; "'#{@id}'"; end
  def get_children; []; end
end
