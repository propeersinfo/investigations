# Parse tree nodes.
# Once built such a tree could be evaluated.

class ParseNode
  def eval(context)
    raise "eval is not implemented for class #{self.class}"
  end

  # declare children nodes; useful for tree pretty print
  def children()
    raise "get_children is not implemented for class #{self.class}"
  end
end

###################################

class FuncDef < ParseNode
  def initialize(id, arglist, block)
    @id = id
    @arglist = arglist
    @block = block
  end

  def to_s(); "#{self.class}(id=#{@id} args=#{@arglist} block=#{@block})" end

  def children; [ @arglist, @block ] end

  def eval(context)
    raise "attach this function to context - that's all"
  end
end

###################################

class SourceUnit < ParseNode
  def initialize(statements)
    @statements = statements
  end

  def to_s; "#{self.class}"; end

  def children; @statements; end

  def eval(context)
    @statements.map do |e|
      e.eval(context)
    end
  end
end

###################################

class Block < ParseNode
  def initialize(statements)
    @statements = statements
  end

  def to_s; "#{self.class}" end

  def children; @statements end

  def eval(context)
    @statements.map do |e|
      e.eval(context)
    end
  end
end

###################################

class Statement < ParseNode
  def initialize(underlying)
    @underlying = underlying
  end

  def to_s; "#{self.class}"; end

  def children; [@underlying]; end

  def eval(context)
    stmt_value = @underlying.eval(context)
    puts "stmt> #{stmt_value}"
  end
end

###################################

# Represents expressions like 'a = b = c' or just 'a'
class Assignment < ParseNode
  def initialize(elements)
    raise "At least one element expected" unless (elements.size > 0)
    @elements = elements
  end

  def to_s; "#{self.class}[#{@elements.size}]"; end

  def children; @elements; end

  def eval(context)
    # evaluate the most right element
    rvalue = @elements.last.eval(context)
    # assign tat value to all the preceding elements
    @elements.reverse[1..-1].each do |e|
      raise "Only IdUse node is supported as rvalue" if e.class.to_s != "IdUse"
      puts "Assigning #{e} = #{rvalue}"
      #puts "  lvalue = #{e.class.to_s} with id = #{e.id}"
      rt_var = context.get_id_or_create_local(e.id)
      rt_var.assign(rvalue)
    end
    rvalue
  end
end

###################################

class Addition < ParseNode
  def initialize(elements)
    @elements = elements
  end

  def to_s; "#{self.class}[#{@elements.size}]"; end

  def children; @elements; end

  def eval(context)
    "<dummy eval result for #{self.class}>"
  end
end

###################################

class IdUse < ParseNode
  attr_reader :id
  def initialize(id)
    @id = id
  end
  def to_s; "Id:#{@id}" end
  def children; [] end
end

###################################

class NumLiteralFunc < ParseNode
  def initialize(value)
    @value = value
  end
  def to_s; "#{self.class}(#{@value})" end
  def children; [] end
  def eval(context)
    self
  end
end

###################################

class StringLiteral < ParseNode
  def initialize(value)
    @value = value
  end
  def to_s; "Str:#{@value}" end
  def children; [] end
end