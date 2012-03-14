# Stuff related to runtime evaluation of code

class EvaluationContext
  def initialize(parent_context = nil)
    @parent_context = parent_context
    @locals = {}
  end

  def enter
  end

  def leave
  end

#  # 'object' is a node referencing a variable or function in interpreted input
#  def add_id(id, object)
#    @locals[id] = object
#  end

  def get_id(id)
    result = @locals[id]
    if result
      result
    elsif @parent_context
      @parent_context.get_id(id)
    else
      nil
    end
  end

  def get_id_or_create_local(id)
    var = self.get_id(id)
    if !var
      #puts "Creating local variable #{id}"
      var = @locals[id] = RuntimeVar.new(id)
    end
    var
  end
end

class RuntimeVar
  def initialize(id, value = nil)
    @id = id
    @value = value
  end
  def to_s
    "#{self.class}(#{id},?)"
  end

  def assign(value)
    #puts "Assigning x = #{value}"
    @value = value
  end
end


class RuntimeValue
  def initialize()
  end
end