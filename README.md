# XMLLang
Converts XML files to Python AST.

## Execute
```
python -m xmllang.compiler exec PATH_TO_XMLFILE.xml
```

## Syntax
### Elements
```xml
<e>13</e> Integer
<e>Batuhan</e> String
<e cast="str">14</e> String
<e cast="bytes" encoding="ASCII">a</e> Bytes
<e cast="bytes">\xc5\x9f</e> Bytes
<e>...</e> Ellipsis
<e>True</e> Bool
<e>None</e> NoneType
```

### Sequence Types
```xml
<list>
    <e>1</e>
    <e>2</e>
    <e>3</e>
</list>
<tuple>
    <e>1</e>
</tuple>
<set>
    <e>2</e>
</set>
```

### Mapping Types
```xml
<dict>
    <item name="KEY">VALUE</item>
    <item name="age">15</item>
    <item name="people">
        <list>
            <e>Batuhan</e>
            <e>Osman</e>
        </list>
    </item>
</dict>
```

### Names
```xml
<a>5</a> a = 5
<print call="True">
    <e>
        <a/>
    </e>
</print> print(a)

<print call="True">
    <e>
        <a>
            <attr name="__doc__">
            <attr name="strip" call="True" />
            <attr name="split" call="True">
                <e>;</e>
                <item name="n">x</item>
            </attr>
        </a>
    </e>
</print> print(a.__doc__.strip().split(;, n='x'))

<a>
    <type call="True">
        <e>A</e>
        <e><tuple></tuple></e>
        <e><dict></dict></e>
    </type>
</a>
<a>
    <attr name="test">
        Hello
    </attr>
</a>
<print call="True">
    <e>
        <a>
            <attr name="test"></attr>
        </a>
    </e>
</print> print(a.test) => 'Hello'
```
