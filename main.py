from miniz.function import Function, Parameter
from miniz.type_system import Boolean, Type

fn = Function(None, "foo")
print(fn)

fn.name = None

print(fn)

fn.name = "bar"
fn.return_type = "i32"
fn.positional_parameters.append(Parameter("a", "i32"))
fn.positional_parameters.append(Parameter("b", "i32", "5"))

print(fn)

c = Parameter("c")
print("c.owner:", c.owner)
fn.named_parameters.append(c)
print("c.owner:", c.owner)

try:
    fn.positional_parameters.append(c)
except ValueError as e:
    print("Exception:", *e.args)
else:
    raise Exception("Expected an exception but it wasn't raised!")

fn.named_parameters.append(Parameter("d", Boolean, Boolean.FalseInstance))

print(fn)

fn.named_parameters.remove(c)
print("c.owner:", c.owner)

fn.variadic_positional_parameter = Parameter("args")

print(fn)

fn.variadic_named_parameter = Parameter("kwargs", Type)

print(fn)

fn.variadic_positional_parameter = None

print(fn)
print(fn.variadic_named_parameter.owner)
