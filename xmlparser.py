import inspect
from abc import ABC

class AbstractParser(ABC):
    """Xml parser.

        Given a model, tag, set of relative paths for this tag to data and external parameters,
         build a model object

        1) There are 4 stages of building a model.

            a) Collecting raw data from xml
            b) Handling the data
            c) Getting model parameters from handled data
            d) Validation of model params
            e) Save of model

        2) For these stages there is next interface:

            i) In the outset, next class attributes should be defined in successor class

             data : set - class attribute which gives names to the raw data

             internal_attr_data: set - class attribute which defines which names from "data" set relates to data which
                is attribute of some tag

             external_data: set - class attribute which defines which names from "data" set relates to data which is
                passed as external parameters to constructor

             Model: object with some fields and save method - model which is built

             model_params: set - class attribute which contains the names of arguments for construction of a model

            Now you understand how to pass arguments to constructor.

            Firstly, it is necessary to pass tag (<class 'xml.etree.ElementTree.Element'>) which contains all internal data
            Secondly, you pass all passes to the data, which you defined in "data" set

                if it is internal data, which is text inside some tag, then you pass relative path for defined earlier
                 root tag to this tag.

                if it is internal data, which is attribute of some tag, then you pass tuple (<relative path for defined earlier
                 root tag to this tag>, <name of attribute>)

                if it is external data, then you pass it as it is

            Ex:

                xml:

                <student num="3">
                    <name>Michiel</name>
                    <surname>
                        Gordon
                    </surname>
                    <education>
                        <university city="Moscow">
                            HSE university
                        </university>
                    </education>
                </student>


                class MyParser(AbstractParser):

                    data = {"name", "surname", "university", "number", "birthplace", city}
                    internal_attr_data = {"number", city}
                    external_data = {"birthplace"}

                    model_params = {"fullname, "university", "number", "birthplace", "city" }

                    ...


                # assume that root is student tag and birthplace0 is defined
                parser = MyParser(root, name="name", surname="surname", number=("", "num"),
                 city=("education/university", "city"), university="education/university",
                 birthplace=birthplace0
                )

            ii) For stage "Handling data" in successor class, handlers as static methods should be defined

                Ex:

                if data = {"weight", "length", "height", ...}

                then to handle "weight" data there must be defined method:

                 @staticmethod
                 def weight_handler(weight):
                    <some handler logic>

                or it is possible also to assign external function to variable with name "weight_handler"

                 weight_handler = external_function
                 ...

                By default, if you have not defined handler for some data, data will not be handled

            iii) For stage "Getting model parameters from handled data" in successor class, "from-function" as static
             methods should be defined

                a)

                Ex:

                if  data = {"width", "length", "height", ...}
                    model_params = {"volume"}

                then to get volume param there must be defined method:

                    @staticmethod
                    def volume_from(weight, width, height):
                        <some logic>
                        ...
                b)

                By default, if you have not defined from function for some param,
                 param will be equal data with the same name

                Ex:

                if  data = {"width", "length", "height", ...}
                    model_params = {"width", "length", "height", ...}

                and there are not from functions for these params, they will equal to data with the same name.

                Note: Sometimes you want to validate data during handling. You can use ValidationFail from
                 this class as exception for tracking undesired cases.

            iv) For stage "Validation of model params" in successor class, "validate-function" as static
             methods should be defined

                Ex:
                    model_params = {"volume"}

                then to get volume param there must be defined method:

                    @staticmethod
                    def volume_from(weight, width, height):
                        <some logic>
                        ...

                if some parameters are not valid you can use ValidationFail from this class

            v) To save all params of model parser use save method of model.

        """
    external_data = set()
    internal_attr_data = set()

    @staticmethod
    def __find_tag(root, rel_path):
        if rel_path == "":
            return root
        return root.find(rel_path)

    @staticmethod
    def __get_text(tag):
        return None if tag.text is None else tag.text.strip()

    @staticmethod
    def __get_attr(tag, attr):
        return tag.attrib.get(attr, None)

    @staticmethod
    def __default_handler(data_value):
        return data_value

    @staticmethod
    def __default_from(data_value):
        return data_value

    class OddArguments(TypeError):
        pass

    class OddPath(TypeError):
        pass

    class OddFromFunc(TypeError):
        pass

    class ValidationFail(ValueError):
        pass

    @classmethod
    def __validate_path(cls, data, data_path):
        pass

    @classmethod
    def __validate_args(cls, kwargs):
        _data = cls.data.copy()
        for k in kwargs:
            try:
                _data.remove(k)
            except KeyError:
                raise cls.OddArguments(f" data set in {cls.__name__} does not contain \"{k}\" argument")
        if _data:
            raise cls.OddArguments(f"{_data} pathes were not passed")

        for data, data_path in kwargs.items():
            cls.__validate_path(data, data_path)

    def __init__(self, root, **kwargs):

        cls = self.__class__

        if not hasattr(cls, 'data'):
            cls.data = cls.model_params.copy()
        if not hasattr(cls, 'internal_data'):
            cls.internal_data = cls.data.difference(cls.external_data | cls.internal_attr_data)

        cls.__validate_args(kwargs)

        self.instance_data = {}
        self.tag = root
        for data in cls.data:
            if data in cls.external_data:
                self.instance_data[data] = kwargs[data]
            if data in cls.internal_attr_data:
                path, attr = kwargs[data]
                tag = cls.__find_tag(root, path)

                self.instance_data[data] = cls.__get_attr(tag, attr) if tag is not None else None

            if data in cls.internal_data:
                path = kwargs[data]
                tag = cls.__find_tag(root, path)
                self.instance_data[data] = cls.__get_text(tag) if tag is not None else None

        static_methods = dict(inspect.getmembers(cls, inspect.isfunction))

        self.handled_data = {}
        for name, value in self.instance_data.items():
            handler = static_methods.get(name + "_handler", cls.__default_handler)
            self.handled_data[name] = handler(value)

        self.instance_model_params = {}
        for param in cls.model_params:

            try:
                param_from = static_methods[param + "_from"]
            except KeyError:
                param_from = cls.__default_from
                self.instance_model_params[param] = param_from(self.handled_data[param])
            else:
                args = inspect.getfullargspec(param_from)[0]
                args_values = []
                for a in args:
                    try:
                        args_values.append(self.handled_data[a])
                    except KeyError:
                        raise cls.OddFromFunc(f"{param}_from function has argument {a} not included in data")
                self.instance_model_params[param] = param_from(*args_values)

        for param in cls.model_params:
            try:
                validate = static_methods["validate_" + param]
                validate(self.instance_model_params[param])
            except KeyError:
                pass

        try:
            validate_all = static_methods["validate"]
        except KeyError:
            pass
        else:
            args = inspect.getfullargspec(validate_all)[0]
            args_values = []
            for a in args:
                try:
                    args_values.append(self.instance_model_params[a])
                except KeyError:
                    raise cls.OddFromFunc(f"validate function has argument {a} not included in model_params")
            validate_all(*args_values)

        self.model = self.Model(**self.instance_model_params)

    def save(self):
        return self.model.save()

    def get_model(self):
        return self.model

    def get_tag(self):
        return self.tag

    def _get_raw_data(self, data):
        return self.instance_data[data]

    def _get_handled_data(self, data):
        return self.handled_data[data]

    def _get_model_param(self, param):
        return self.instance_model_params[param]


class AbstractDjangoParser(AbstractParser):
    """Xml parser for Django.

    Everything is the same as in AbstractParser(read its docstring), but models_params are fields of model.
    If you do not want take all fields in model_params, you can exlude them
    by adding their names in "exclude_model_params" set
    """
    exclude_model_params = {"id"}

    def __init__(self, root, **kwargs):

        cls = self.__class__
        if not hasattr(cls, "model_params"):
            from django.db.models.fields.related import ForeignKey
            model_fileds = set()
            for f in cls.Model._meta.fields:
                if isinstance(f, ForeignKey):
                    model_fileds.add(f.attname[:-3])  # get rid of "_id" in field_name
                else:
                    model_fileds.add(f.attname)
            cls.model_params = model_fileds - cls.exclude_model_params

        super().__init__(root, **kwargs)