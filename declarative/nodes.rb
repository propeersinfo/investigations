# Parse tree nodes.
# Once built such a tree could be evaluated.

class Node
  def eval(context)
    raise "eval is not implemented for class #{self.class}"
  end
end

class FuncDef < Node
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

class Block < Node
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

class Assignment < Node
  def initialize(elements)
    @elements = elements
  end
  def to_s
    #"#{self.class}(#{@elements.join(',')})"
    "#{self.class}[#{@elements.size}]"
  end
  def get_children; [ @elements ]; end
end

class Addition < Node
  def initialize(elements)
    @elements = elements
  end
  def to_s
    #"#{self.class}(#{@elements.join('+')})"
    "#{self.class}[#{@elements.size}]"
  end
  def get_children
    [ @elements ]
  end
end

class IdUse < Node
  def initialize(id)
    @id = id
  end
  def to_s
    "'#{@id}'"
  end
  def get_children; []; end
end
