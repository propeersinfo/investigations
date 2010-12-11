# Stuff related to runtime evaluation of code

class Value
  
end

class EvaluationContext
  def initialize(parentContext = nil)
    @parentContext = parentContext
    @ids = {}
  end

  # 'object' is a node referencing a variable or function in interpreted input
  def addId(id, object)
    @ids[id] = object
  end

  def getId(id)
    result = @ids[id]
    if result
      result
    elsif @parentContext
      @parentContext.getId(id)
    else
      return nil
    end
  end
end