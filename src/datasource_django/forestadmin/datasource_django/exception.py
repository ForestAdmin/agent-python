from forestadmin.datasource_toolkit.exceptions import DatasourceToolkitException


class DjangoDatasourceException(DatasourceToolkitException):
    pass


class DjangoNativeDriver(DjangoDatasourceException):
    pass
