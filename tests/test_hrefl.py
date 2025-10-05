"""
Unit tests for Heath's __hrefl

Tests:
- __hrefl: unified reflection annotation for all declaration types
"""

import pytest
from cxxheaderparser.parser import CxxParser
from cxxheaderparser.visitor import CxxVisitor
from cxxheaderparser.types import EnumDecl, ClassDecl, Function, Field, Variable


class HReflTestVisitor(CxxVisitor):
    """Visitor that collects parsed declarations for testing"""
    
    def __init__(self):
        self.classes = []
        self.enums = []
        self.functions = []
        self.fields = []
        self.variables = []
    
    def on_class_start(self, state):
        self.classes.append(state.class_decl)
        return True
    
    def on_enum(self, state, enum):
        self.enums.append(enum)
    
    def on_function(self, state, fn):
        self.functions.append(fn)
    
    def on_class_field(self, state, field):
        self.fields.append(field)
    
    def on_variable(self, state, var):
        self.variables.append(var)


class TestHReflParsing:
    """Test cases for __hrefl functionality"""
    
    def test_class_annotation_parsing(self):
        """Test that __hrefl annotations are parsed correctly for classes"""
        content = """
        __hrefl(class_prop=class_val, type=widget)
        class TestClass {
        public:
            int member;
        };
        """
        
        visitor = HReflTestVisitor()
        parser = CxxParser("test.h", content, visitor)
        parser.parse()
        
        assert len(visitor.classes) == 1
        cls = visitor.classes[0]
        
        assert cls.hrefl is not None
        assert "class_prop" in cls.hrefl
        assert "type" in cls.hrefl
        assert cls.hrefl["class_prop"].format() == "class_val"
        assert cls.hrefl["type"].format() == "widget"
    
    def test_enum_annotation_parsing(self):
        """Test that __hrefl annotations are parsed correctly for enums"""
        content = """
        __hrefl(enum_prop=enum_val, serializable=true)
        enum TestEnum { A, B, C };
        """
        
        visitor = HReflTestVisitor()
        parser = CxxParser("test.h", content, visitor)
        parser.parse()
        
        assert len(visitor.enums) == 1
        enum = visitor.enums[0]
        
        assert enum.hrefl is not None
        assert "enum_prop" in enum.hrefl
        assert "serializable" in enum.hrefl
        assert enum.hrefl["enum_prop"].format() == "enum_val"
        assert enum.hrefl["serializable"].format() == "true"
    
    def test_function_annotation_parsing(self):
        """Test that __hrefl annotations are parsed correctly for functions"""
        content = """
        __hrefl(func_prop=func_val, exported=true)
        void test_function(int x);
        """
        
        visitor = HReflTestVisitor()
        parser = CxxParser("test.h", content, visitor)
        parser.parse()
        
        assert len(visitor.functions) == 1
        func = visitor.functions[0]
        
        assert func.hrefl is not None
        assert "func_prop" in func.hrefl
        assert "exported" in func.hrefl
        assert func.hrefl["func_prop"].format() == "func_val"
        assert func.hrefl["exported"].format() == "true"
    
    def test_field_annotation_parsing(self):
        """Test that __hrefl annotations are parsed correctly for class fields"""
        content = """
        class TestClass {
        public:
            __hrefl(field_prop=field_val, bindable=true)
            int member;
            
            int regular_member;
        };
        """
        
        visitor = HReflTestVisitor()
        parser = CxxParser("test.h", content, visitor)
        parser.parse()
        
        assert len(visitor.fields) == 2
        
        # Find the annotated field
        annotated_field = None
        regular_field = None
        
        for field in visitor.fields:
            if field.name == "member":
                annotated_field = field
            elif field.name == "regular_member":
                regular_field = field
        
        assert annotated_field is not None
        assert regular_field is not None
        
        # Check annotated field has __hrefl data
        assert annotated_field.hrefl is not None
        assert "field_prop" in annotated_field.hrefl
        assert "bindable" in annotated_field.hrefl
        assert annotated_field.hrefl["field_prop"].format() == "field_val"
        assert annotated_field.hrefl["bindable"].format() == "true"
        
        # Check regular field has no __hrefl data
        assert regular_field.hrefl is None
    
    def test_variable_no_hrefl(self):
        """Test that global variables do not have __hrefl attribute"""
        content = """
        int global_var = 42;
        """
        
        visitor = HReflTestVisitor()
        parser = CxxParser("test.h", content, visitor)
        parser.parse()
        
        assert len(visitor.variables) == 1
        var = visitor.variables[0]
        
        # Variables should not have __hrefl attribute
        assert not hasattr(var, '__hrefl')
    
    def test_empty_hrefl_annotation(self):
        """Test empty __hrefl annotations"""
        content = """
        __hrefl()
        class EmptyAnnotation {
        public:
            int member;
        };
        """
        
        visitor = HReflTestVisitor()
        parser = CxxParser("test.h", content, visitor)
        parser.parse()
        
        assert len(visitor.classes) == 1
        cls = visitor.classes[0]
        
        assert cls.hrefl is not None
        assert len(cls.hrefl) == 0
    
    def test_multiple_hrefl_properties(self):
        """Test multiple properties in a single __hrefl annotation"""
        content = """
        __hrefl(prop1=val1, prop2=val2, prop3=val3, flag)
        class MultiProps {
        };
        """
        
        visitor = HReflTestVisitor()
        parser = CxxParser("test.h", content, visitor)
        parser.parse()
        
        assert len(visitor.classes) == 1
        cls = visitor.classes[0]
        
        assert cls.hrefl is not None
        assert len(cls.hrefl) == 4
        assert cls.hrefl["prop1"].format() == "val1"
        assert cls.hrefl["prop2"].format() == "val2"
        assert cls.hrefl["prop3"].format() == "val3"
        assert cls.hrefl["flag"] is None  # Flag without value
    
    def test_mixed_annotated_and_regular_declarations(self):
        """Test that annotated and regular declarations coexist correctly"""
        content = """
        __hrefl(annotated=true)
        class AnnotatedClass {
        public:
            __hrefl(special=field)
            int annotated_member;
            
            int regular_member;
        };
        
        class RegularClass {
        public:
            int member;
        };
        
        __hrefl(api=public)
        void annotated_function();
        
        void regular_function();
        
        __hrefl(values=important)
        enum AnnotatedEnum { A, B };
        
        enum RegularEnum { X, Y };
        """
        
        visitor = HReflTestVisitor()
        parser = CxxParser("test.h", content, visitor)
        parser.parse()
        
        # Check classes
        assert len(visitor.classes) == 2
        annotated_class = next((c for c in visitor.classes if c.typename.format() == "class AnnotatedClass"), None)
        regular_class = next((c for c in visitor.classes if c.typename.format() == "class RegularClass"), None)
        
        assert annotated_class is not None
        assert regular_class is not None
        
        assert annotated_class.hrefl is not None
        assert annotated_class.hrefl["annotated"].format() == "true"
        assert regular_class.hrefl is None
        
        # Check functions
        assert len(visitor.functions) == 2
        annotated_func = next((f for f in visitor.functions if f.name.format() == "annotated_function"), None)
        regular_func = next((f for f in visitor.functions if f.name.format() == "regular_function"), None)
        
        assert annotated_func is not None
        assert regular_func is not None
        
        assert annotated_func.hrefl is not None
        assert annotated_func.hrefl["api"].format() == "public"
        assert regular_func.hrefl is None
        
        # Check enums
        assert len(visitor.enums) == 2
        annotated_enum = next((e for e in visitor.enums if e.typename.format() == "enum AnnotatedEnum"), None)
        regular_enum = next((e for e in visitor.enums if e.typename.format() == "enum RegularEnum"), None)
        
        assert annotated_enum is not None
        assert regular_enum is not None
        
        assert annotated_enum.hrefl is not None
        assert annotated_enum.hrefl["values"].format() == "important"
        assert regular_enum.hrefl is None
        
        # Check fields
        assert len(visitor.fields) == 3
        annotated_field = next((f for f in visitor.fields if f.name == "annotated_member"), None)
        regular_field1 = next((f for f in visitor.fields if f.name == "regular_member"), None)
        regular_field2 = next((f for f in visitor.fields if f.name == "member"), None)
        
        assert annotated_field is not None
        assert regular_field1 is not None
        assert regular_field2 is not None
        
        assert annotated_field.hrefl is not None
        assert annotated_field.hrefl["special"].format() == "field"
        assert regular_field1.hrefl is None
        assert regular_field2.hrefl is None


class TestUnifiedHReflKeyword:
    """Test the unified __hrefl keyword"""
    
    def test_unified_keyword_recognized(self):
        """Test that the __hrefl keyword is recognized for all declaration types"""
        content = """
        __hrefl(generic=true)
        class GenericClass {};
        
        __hrefl(class_specific=true)
        class ClassSpecific {};
        
        __hrefl(func_specific=true)
        void func();
        
        __hrefl(enum_specific=true)
        enum EnumSpecific { A };
        
        class Container {
        public:
            __hrefl(property_specific=true)
            int field;
        };
        """
        
        visitor = HReflTestVisitor()
        parser = CxxParser("test.h", content, visitor)
        parser.parse()
        
        # All should be parsed without errors
        assert len(visitor.classes) == 3
        assert len(visitor.functions) == 1
        assert len(visitor.enums) == 1
        assert len(visitor.fields) == 1
        
        # Check that all have their respective __hrefl data
        generic_class = next((c for c in visitor.classes if c.typename.format() == "class GenericClass"), None)
        class_specific = next((c for c in visitor.classes if c.typename.format() == "class ClassSpecific"), None)
        
        assert generic_class.hrefl["generic"].format() == "true"
        assert class_specific.hrefl["class_specific"].format() == "true"
        assert visitor.functions[0].hrefl["func_specific"].format() == "true"
        assert visitor.enums[0].hrefl["enum_specific"].format() == "true"
        assert visitor.fields[0].hrefl["property_specific"].format() == "true"


if __name__ == "__main__":
    pytest.main([__file__])
