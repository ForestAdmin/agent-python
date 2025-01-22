## [1.22.1](https://github.com/ForestAdmin/agent-python/compare/v1.22.0...v1.22.1) (2025-01-22)


### Bug Fixes

* **action_hook:** parsing int collection pk on action hook ([#308](https://github.com/ForestAdmin/agent-python/issues/308)) ([9f89903](https://github.com/ForestAdmin/agent-python/commit/9f89903f5deafb4a697958509e53c98aa2d7c9b6))

# [1.22.0](https://github.com/ForestAdmin/agent-python/compare/v1.21.0...v1.22.0) (2025-01-06)


### Features

* support python 3.13 ([#306](https://github.com/ForestAdmin/agent-python/issues/306)) ([5dad5e3](https://github.com/ForestAdmin/agent-python/commit/5dad5e31b7bb85108bda23c8cc56c517ed21552c))

# [1.21.0](https://github.com/ForestAdmin/agent-python/compare/v1.20.1...v1.21.0) (2025-01-06)


### Features

* **django:** support django 5.1 ([#272](https://github.com/ForestAdmin/agent-python/issues/272)) ([efe61e7](https://github.com/ForestAdmin/agent-python/commit/efe61e7faa8aab968f14178ff222bb2a42c8d5a1))

## [1.20.1](https://github.com/ForestAdmin/agent-python/compare/v1.20.0...v1.20.1) (2025-01-06)


### Performance Improvements

* add aggregate to lazy join ([#298](https://github.com/ForestAdmin/agent-python/issues/298)) ([692879a](https://github.com/ForestAdmin/agent-python/commit/692879a80e07cb8460080c867067827ab194dd19))

# [1.20.0](https://github.com/ForestAdmin/agent-python/compare/v1.19.1...v1.20.0) (2024-12-20)


### Features

* **rename:** rename collection can be a function ([#291](https://github.com/ForestAdmin/agent-python/issues/291)) ([cc8cb99](https://github.com/ForestAdmin/agent-python/commit/cc8cb99e0ece3b1857370fd37a2c9749c4bb598d))

## [1.19.1](https://github.com/ForestAdmin/agent-python/compare/v1.19.0...v1.19.1) (2024-12-20)


### Bug Fixes

* **operator_capabilities:** operator emulation wasn't expose to front end ([#301](https://github.com/ForestAdmin/agent-python/issues/301)) ([0e95a58](https://github.com/ForestAdmin/agent-python/commit/0e95a58be6dcb0ae7d92d9929cedbf0c63a7fc8e))

# [1.19.0](https://github.com/ForestAdmin/agent-python/compare/v1.18.6...v1.19.0) (2024-12-19)


### Features

* **capabilities:** support for native query connections ([#290](https://github.com/ForestAdmin/agent-python/issues/290)) ([1e43231](https://github.com/ForestAdmin/agent-python/commit/1e4323199faef1192430c56758879ae1b0b45fd1))

## [1.18.6](https://github.com/ForestAdmin/agent-python/compare/v1.18.5...v1.18.6) (2024-12-16)


### Bug Fixes

* **lazy_join:** handle nullable relation ([#296](https://github.com/ForestAdmin/agent-python/issues/296)) ([fc4a2af](https://github.com/ForestAdmin/agent-python/commit/fc4a2af52415c6c26795e4be9344a4c0e0d06bbe))

## [1.18.5](https://github.com/ForestAdmin/agent-python/compare/v1.18.4...v1.18.5) (2024-12-10)


### Performance Improvements

* **table_join:** avoid join if we only want the target field of the relation ([#293](https://github.com/ForestAdmin/agent-python/issues/293)) ([a6a4739](https://github.com/ForestAdmin/agent-python/commit/a6a4739bd97cb47768007241751c60421b70ed39))

## [1.18.4](https://github.com/ForestAdmin/agent-python/compare/v1.18.3...v1.18.4) (2024-11-28)


### Bug Fixes

* **rename decorator:** properly map relation when renaming pk field ([#292](https://github.com/ForestAdmin/agent-python/issues/292)) ([ac9f63e](https://github.com/ForestAdmin/agent-python/commit/ac9f63efe9a7728c1da012059fcab0d436143940))

## [1.18.3](https://github.com/ForestAdmin/agent-python/compare/v1.18.2...v1.18.3) (2024-11-22)


### Bug Fixes

* **security:** patch micromatch dependency vulnerabilities ([#289](https://github.com/ForestAdmin/agent-python/issues/289)) ([713d267](https://github.com/ForestAdmin/agent-python/commit/713d267364f1378bef293545e0cfb0dfa1ae8646))

## [1.18.2](https://github.com/ForestAdmin/agent-python/compare/v1.18.1...v1.18.2) (2024-11-18)


### Bug Fixes

* **permission:** get approval conditions by role id ([#286](https://github.com/ForestAdmin/agent-python/issues/286)) ([8853290](https://github.com/ForestAdmin/agent-python/commit/8853290a9a4406f54170d020d85b78cbfa803db2))

## [1.18.1](https://github.com/ForestAdmin/agent-python/compare/v1.18.0...v1.18.1) (2024-11-08)


### Bug Fixes

* **native_driver:** usage is now the same in django and sqlalchemy ([#285](https://github.com/ForestAdmin/agent-python/issues/285)) ([b221271](https://github.com/ForestAdmin/agent-python/commit/b22127124e2b87ae2dca8335618caa4d0dbc7e5e))

# [1.18.0](https://github.com/ForestAdmin/agent-python/compare/v1.17.0...v1.18.0) (2024-10-31)


### Features

* add request ip to user context ([#280](https://github.com/ForestAdmin/agent-python/issues/280)) ([24e5b9c](https://github.com/ForestAdmin/agent-python/commit/24e5b9c178a7ce1e58917a3a997f97feb3bfe8d0))

# [1.17.0](https://github.com/ForestAdmin/agent-python/compare/v1.16.3...v1.17.0) (2024-10-24)


### Features

* **capabilities:** expose fields operators to frontend ([#279](https://github.com/ForestAdmin/agent-python/issues/279)) ([baba981](https://github.com/ForestAdmin/agent-python/commit/baba981d03eb4fac4da639a42ab0d694e48509d0))

## [1.16.3](https://github.com/ForestAdmin/agent-python/compare/v1.16.2...v1.16.3) (2024-10-23)


### Bug Fixes

* **serialization:** add one to many in relations in json api serialization ([#281](https://github.com/ForestAdmin/agent-python/issues/281)) ([d410323](https://github.com/ForestAdmin/agent-python/commit/d410323a7c7d75f029a70c94394245b38ad6b327))

## [1.16.2](https://github.com/ForestAdmin/agent-python/compare/v1.16.1...v1.16.2) (2024-10-16)


### Bug Fixes

* **update:** the generated sql request always sets the primary key by its own value ([#275](https://github.com/ForestAdmin/agent-python/issues/275)) ([cdf700f](https://github.com/ForestAdmin/agent-python/commit/cdf700fff434caa8644a6a49049a8aa156a4984a))

## [1.16.1](https://github.com/ForestAdmin/agent-python/compare/v1.16.0...v1.16.1) (2024-10-09)


### Bug Fixes

* **permissions:** properly check permissions when dissociating or deleting related resources ([#278](https://github.com/ForestAdmin/agent-python/issues/278)) ([e8123c1](https://github.com/ForestAdmin/agent-python/commit/e8123c1875055d11d2ef8ff6b2a56d4d5b6b976a))

# [1.16.0](https://github.com/ForestAdmin/agent-python/compare/v1.15.1...v1.16.0) (2024-10-09)


### Features

* **action:** allow forms with layout to be static ([#277](https://github.com/ForestAdmin/agent-python/issues/277)) ([cafd0f5](https://github.com/ForestAdmin/agent-python/commit/cafd0f5790449f08cdf864b6879183cd3d6a18d2))

## [1.15.1](https://github.com/ForestAdmin/agent-python/compare/v1.15.0...v1.15.1) (2024-10-09)


### Bug Fixes

* **action:** search field didn't works with row and pages ([#276](https://github.com/ForestAdmin/agent-python/issues/276)) ([e0c3d64](https://github.com/ForestAdmin/agent-python/commit/e0c3d64f626f120e8549219e7b9a6e8be89a9dab))

# [1.15.0](https://github.com/ForestAdmin/agent-python/compare/v1.14.0...v1.15.0) (2024-10-09)


### Features

* **actions:** add pages in forms  ([#274](https://github.com/ForestAdmin/agent-python/issues/274)) ([d591fdd](https://github.com/ForestAdmin/agent-python/commit/d591fdd2e9f6e477a0374ff0090deeafb113b464))

# [1.14.0](https://github.com/ForestAdmin/agent-python/compare/v1.13.0...v1.14.0) (2024-10-04)


### Features

* **action:** add description and submit button label to action ([#273](https://github.com/ForestAdmin/agent-python/issues/273)) ([2009427](https://github.com/ForestAdmin/agent-python/commit/2009427659482b73f238bb3d112e7f26820db31f))

# [1.13.0](https://github.com/ForestAdmin/agent-python/compare/v1.12.0...v1.13.0) (2024-09-30)


### Features

* **action:** add optional id in form fields ([#271](https://github.com/ForestAdmin/agent-python/issues/271)) ([a18b8c1](https://github.com/ForestAdmin/agent-python/commit/a18b8c151f819d90072a4f0f2a07531820378635))

# [1.12.0](https://github.com/ForestAdmin/agent-python/compare/v1.11.0...v1.12.0) (2024-09-25)


### Features

* **action_form:** add row layout customization ([#268](https://github.com/ForestAdmin/agent-python/issues/268)) ([972e445](https://github.com/ForestAdmin/agent-python/commit/972e445314584d8d265d5b76b4f380079490ce1f))

# [1.11.0](https://github.com/ForestAdmin/agent-python/compare/v1.10.2...v1.11.0) (2024-09-23)


### Features

* **form_customization:** add html block layout element ([#267](https://github.com/ForestAdmin/agent-python/issues/267)) ([f250799](https://github.com/ForestAdmin/agent-python/commit/f250799b62164f2360e201a55e22a8004baf1977))

## [1.10.2](https://github.com/ForestAdmin/agent-python/compare/v1.10.1...v1.10.2) (2024-09-23)


### Bug Fixes

* **action:** having a default value on file field make the form dynamic ([#270](https://github.com/ForestAdmin/agent-python/issues/270)) ([4dcf132](https://github.com/ForestAdmin/agent-python/commit/4dcf13265b65d4295a36758e3ff5169ba5330236))

## [1.10.1](https://github.com/ForestAdmin/agent-python/compare/v1.10.0...v1.10.1) (2024-09-23)


### Bug Fixes

* **action:** load hook with collection field raise error ([#269](https://github.com/ForestAdmin/agent-python/issues/269)) ([c772d87](https://github.com/ForestAdmin/agent-python/commit/c772d87fbc64b318baa44ce3f471487bfab1a789))

# [1.10.0](https://github.com/ForestAdmin/agent-python/compare/v1.9.1...v1.10.0) (2024-09-16)


### Features

* **form_customization:** add separators ([#265](https://github.com/ForestAdmin/agent-python/issues/265)) ([6947bc6](https://github.com/ForestAdmin/agent-python/commit/6947bc6bb399a50fd97bb283bdc66bd72c760f3c))

## [1.9.1](https://github.com/ForestAdmin/agent-python/compare/v1.9.0...v1.9.1) (2024-09-12)


### Bug Fixes

* **action_error_html:** html content when execute return error is now sent correctly ([#266](https://github.com/ForestAdmin/agent-python/issues/266)) ([121af4c](https://github.com/ForestAdmin/agent-python/commit/121af4ca4bbad37b159d7df464d673a7e4dde899))

# [1.9.0](https://github.com/ForestAdmin/agent-python/compare/v1.8.23...v1.9.0) (2024-08-22)


### Features

* add polymophism support ([#231](https://github.com/ForestAdmin/agent-python/issues/231)) ([950aed2](https://github.com/ForestAdmin/agent-python/commit/950aed2243e584ee027508db38393912ead32dc1))

## [1.8.23](https://github.com/ForestAdmin/agent-python/compare/v1.8.22...v1.8.23) (2024-08-05)


### Bug Fixes

* **jsonapi:** ignore empty relationships for creation and edition ([#256](https://github.com/ForestAdmin/agent-python/issues/256)) ([7767e70](https://github.com/ForestAdmin/agent-python/commit/7767e7091cc38a96d492621795cb087e5654695a))

## [1.8.22](https://github.com/ForestAdmin/agent-python/compare/v1.8.21...v1.8.22) (2024-08-01)


### Bug Fixes

* **search:** fix parsing number from string in search ([#254](https://github.com/ForestAdmin/agent-python/issues/254)) ([6062cc7](https://github.com/ForestAdmin/agent-python/commit/6062cc73448538744b06aeec5f4d7a1ddd13b95c))

## [1.8.21](https://github.com/ForestAdmin/agent-python/compare/v1.8.20...v1.8.21) (2024-08-01)


### Bug Fixes

* **one_to_one:** no more error when setting the relation to null ([#253](https://github.com/ForestAdmin/agent-python/issues/253)) ([d091f76](https://github.com/ForestAdmin/agent-python/commit/d091f76b59b7134b93af6ea104946798bfa38c4a))

## [1.8.20](https://github.com/ForestAdmin/agent-python/compare/v1.8.19...v1.8.20) (2024-07-31)


### Bug Fixes

* set many to one relation to null ([#252](https://github.com/ForestAdmin/agent-python/issues/252)) ([546c3df](https://github.com/ForestAdmin/agent-python/commit/546c3dff8bf8721d59d90227d183a39edb4f3725))

## [1.8.19](https://github.com/ForestAdmin/agent-python/compare/v1.8.18...v1.8.19) (2024-07-18)


### Bug Fixes

* filters on dateonly ([#251](https://github.com/ForestAdmin/agent-python/issues/251)) ([1626308](https://github.com/ForestAdmin/agent-python/commit/1626308241b4937b8f1230d64869c606b80837ba))

## [1.8.18](https://github.com/ForestAdmin/agent-python/compare/v1.8.17...v1.8.18) (2024-07-17)


### Bug Fixes

* **computed:** computed field as dependency of another works ([#250](https://github.com/ForestAdmin/agent-python/issues/250)) ([d8474d7](https://github.com/ForestAdmin/agent-python/commit/d8474d7a04818786c7b0d1279a2649236be73b52))

## [1.8.17](https://github.com/ForestAdmin/agent-python/compare/v1.8.16...v1.8.17) (2024-07-15)


### Bug Fixes

* **schema:** default_value of a relation is always null ([#249](https://github.com/ForestAdmin/agent-python/issues/249)) ([d37bd8a](https://github.com/ForestAdmin/agent-python/commit/d37bd8a9cf9f52aad73f960f4c5751c787001c17))

## [1.8.16](https://github.com/ForestAdmin/agent-python/compare/v1.8.15...v1.8.16) (2024-07-12)


### Bug Fixes

* **django:** don't create agent when django is launch by mypy ([#242](https://github.com/ForestAdmin/agent-python/issues/242)) ([368cf7c](https://github.com/ForestAdmin/agent-python/commit/368cf7c08cdcd37faddd4159f28a44f109b39d50))

## [1.8.15](https://github.com/ForestAdmin/agent-python/compare/v1.8.14...v1.8.15) (2024-07-10)


### Bug Fixes

* **django_introspection:** supported operators are compliant to django capabilities ([#240](https://github.com/ForestAdmin/agent-python/issues/240)) ([c5cfedf](https://github.com/ForestAdmin/agent-python/commit/c5cfedfa58e4ffa2af6f695f2632b71e285c53df))

## [1.8.14](https://github.com/ForestAdmin/agent-python/compare/v1.8.13...v1.8.14) (2024-07-08)


### Bug Fixes

* **json_api:** regression inserted in 'many to many attachment during creation' ([#238](https://github.com/ForestAdmin/agent-python/issues/238)) ([36ce8a7](https://github.com/ForestAdmin/agent-python/commit/36ce8a7608f7ab2eb45542ebd7d3033f446dc7e4))

## [1.8.13](https://github.com/ForestAdmin/agent-python/compare/v1.8.12...v1.8.13) (2024-07-08)


### Bug Fixes

* **computed:** falsy dependency records were not passed to user function ([#237](https://github.com/ForestAdmin/agent-python/issues/237)) ([c8d683e](https://github.com/ForestAdmin/agent-python/commit/c8d683e1612df2586ca229a386a56e8f192a1c00))

## [1.8.12](https://github.com/ForestAdmin/agent-python/compare/v1.8.11...v1.8.12) (2024-07-04)


### Bug Fixes

* **introspection:** ignore polymorphic fields log is now info ([#236](https://github.com/ForestAdmin/agent-python/issues/236)) ([64ff619](https://github.com/ForestAdmin/agent-python/commit/64ff619f7190f078df0e7d3152ea2b1382f4cc70))

## [1.8.11](https://github.com/ForestAdmin/agent-python/compare/v1.8.10...v1.8.11) (2024-07-03)


### Bug Fixes

* **action_result_file:** filename is now functional ([#235](https://github.com/ForestAdmin/agent-python/issues/235)) ([1e7fa1b](https://github.com/ForestAdmin/agent-python/commit/1e7fa1b8bbd5da4bd09b10d27abf25bac6ef115f))

## [1.8.10](https://github.com/ForestAdmin/agent-python/compare/v1.8.9...v1.8.10) (2024-07-03)


### Bug Fixes

* attach a many to many record during creation ([#234](https://github.com/ForestAdmin/agent-python/issues/234)) ([cd07f67](https://github.com/ForestAdmin/agent-python/commit/cd07f673b1b6aef4e6f9f0f8ae0949968c14a777))

## [1.8.9](https://github.com/ForestAdmin/agent-python/compare/v1.8.8...v1.8.9) (2024-07-02)


### Bug Fixes

* **relation:** many to may dissociation with composite foreign key now works ([#232](https://github.com/ForestAdmin/agent-python/issues/232)) ([0d43f74](https://github.com/ForestAdmin/agent-python/commit/0d43f7422451198912f79f3e61eb24c8a50c6442))

## [1.8.8](https://github.com/ForestAdmin/agent-python/compare/v1.8.7...v1.8.8) (2024-07-02)


### Bug Fixes

* **uuid:** uuid wasn't correctly handled by sqlalchemy 2.0 DS and agent ([#233](https://github.com/ForestAdmin/agent-python/issues/233)) ([5faa9fb](https://github.com/ForestAdmin/agent-python/commit/5faa9fbdae07fb6c2e8dc1933359176baeb047f9))

## [1.8.7](https://github.com/ForestAdmin/agent-python/compare/v1.8.6...v1.8.7) (2024-06-18)


### Bug Fixes

* bad import python 3.8 and 3.9 ([#230](https://github.com/ForestAdmin/agent-python/issues/230)) ([511f30c](https://github.com/ForestAdmin/agent-python/commit/511f30cc4fc7171c98cbac41773e9ba2554dfcf2))

## [1.8.6](https://github.com/ForestAdmin/agent-python/compare/v1.8.5...v1.8.6) (2024-06-14)


### Bug Fixes

* imported fields operators were wrong ([#226](https://github.com/ForestAdmin/agent-python/issues/226)) ([8859fa4](https://github.com/ForestAdmin/agent-python/commit/8859fa4f64bc11298d311fe71e3344b09bb4478a))

## [1.8.5](https://github.com/ForestAdmin/agent-python/compare/v1.8.4...v1.8.5) (2024-06-14)


### Bug Fixes

* **search:** search was always extended ([#225](https://github.com/ForestAdmin/agent-python/issues/225)) ([a28f544](https://github.com/ForestAdmin/agent-python/commit/a28f5446710c7e6dbf1d8db64d093d1d70f14d06))

## [1.8.4](https://github.com/ForestAdmin/agent-python/compare/v1.8.3...v1.8.4) (2024-06-05)


### Bug Fixes

* **authent:** works on multi instances setup ([#224](https://github.com/ForestAdmin/agent-python/issues/224)) ([c31db91](https://github.com/ForestAdmin/agent-python/commit/c31db91771a6f7d58662f8aca3b15c0c72339ba6))

## [1.8.3](https://github.com/ForestAdmin/agent-python/compare/v1.8.2...v1.8.3) (2024-05-29)


### Bug Fixes

* **schema_keys_removal:** remove useless keys ([#221](https://github.com/ForestAdmin/agent-python/issues/221)) ([731a24d](https://github.com/ForestAdmin/agent-python/commit/731a24d543b4ef6c0faca97da8cc2731e0f0b14a))

## [1.8.2](https://github.com/ForestAdmin/agent-python/compare/v1.8.1...v1.8.2) (2024-05-23)


### Bug Fixes

* **datasource_django:** remove direct dependency to postgresql driver ([#222](https://github.com/ForestAdmin/agent-python/issues/222)) ([0b67a77](https://github.com/ForestAdmin/agent-python/commit/0b67a7770eb7cbbc3977f8653730b89da8df447f))

## [1.8.1](https://github.com/ForestAdmin/agent-python/compare/v1.8.0...v1.8.1) (2024-05-14)


### Bug Fixes

* **schema_file:** enum values are now sorted in schema json file ([#219](https://github.com/ForestAdmin/agent-python/issues/219)) ([d42716f](https://github.com/ForestAdmin/agent-python/commit/d42716f1e15d394fffa2560bf80e5f1d045b0a46))

# [1.8.0](https://github.com/ForestAdmin/agent-python/compare/v1.7.0...v1.8.0) (2024-04-30)


### Features

* support multi field sorting from frontend ([#218](https://github.com/ForestAdmin/agent-python/issues/218)) ([2887f94](https://github.com/ForestAdmin/agent-python/commit/2887f94ea18bd9af7858915b3e859fb73d928d2a))

# [1.7.0](https://github.com/ForestAdmin/agent-python/compare/v1.6.8...v1.7.0) (2024-04-25)


### Features

* add override decorator ([#217](https://github.com/ForestAdmin/agent-python/issues/217)) ([56b4ce8](https://github.com/ForestAdmin/agent-python/commit/56b4ce82c6a644c89152aec0d9c7bc2a0df98fbd))

## [1.6.8](https://github.com/ForestAdmin/agent-python/compare/v1.6.7...v1.6.8) (2024-04-18)


### Bug Fixes

* error parsing query for get_record_id ([#216](https://github.com/ForestAdmin/agent-python/issues/216)) ([9e6dfed](https://github.com/ForestAdmin/agent-python/commit/9e6dfed2363fd63e17189b7b1b9ff979abc8d7d0))


### Reverts

* fix of error parsing query has too much side effects ([#214](https://github.com/ForestAdmin/agent-python/issues/214)) ([27bfce6](https://github.com/ForestAdmin/agent-python/commit/27bfce62663df68c6c48139348fc15b11ce0e139))

## [1.6.7](https://github.com/ForestAdmin/agent-python/compare/v1.6.6...v1.6.7) (2024-04-11)


### Bug Fixes

* error parsing query for get_record_id ([#213](https://github.com/ForestAdmin/agent-python/issues/213)) ([03444f1](https://github.com/ForestAdmin/agent-python/commit/03444f17c83623d132872224e74d30043cf3efce))

## [1.6.6](https://github.com/ForestAdmin/agent-python/compare/v1.6.5...v1.6.6) (2024-04-03)


### Bug Fixes

* **smart-field:** dependencies order does not matter anymore in implementation ([#211](https://github.com/ForestAdmin/agent-python/issues/211)) ([c52543c](https://github.com/ForestAdmin/agent-python/commit/c52543c2c25f5ca0de00e76015fd4dd6143806ee))

## [1.6.5](https://github.com/ForestAdmin/agent-python/compare/v1.6.4...v1.6.5) (2024-04-03)


### Bug Fixes

* revert smart fields records are now correctly formed ([#210](https://github.com/ForestAdmin/agent-python/issues/210)) ([2a7ddd1](https://github.com/ForestAdmin/agent-python/commit/2a7ddd1e19d67383d5e06ab24361670bf578c3f2))

## [1.6.4](https://github.com/ForestAdmin/agent-python/compare/v1.6.3...v1.6.4) (2024-04-03)


### Bug Fixes

* **computed:** aggregate on computed raised timezone error ([#209](https://github.com/ForestAdmin/agent-python/issues/209)) ([5d50943](https://github.com/ForestAdmin/agent-python/commit/5d50943cfa5485c1c57cf4d17f4ef5b7e96a6098))

## [1.6.3](https://github.com/ForestAdmin/agent-python/compare/v1.6.2...v1.6.3) (2024-04-03)


### Bug Fixes

* smart fields records are now correctly formed ([#208](https://github.com/ForestAdmin/agent-python/issues/208)) ([79c4e78](https://github.com/ForestAdmin/agent-python/commit/79c4e787dd59e2af0f90369e1a27bb59315f7b50))

## [1.6.2](https://github.com/ForestAdmin/agent-python/compare/v1.6.1...v1.6.2) (2024-04-02)


### Bug Fixes

* **publication_collection:** remove_collections now works ([#206](https://github.com/ForestAdmin/agent-python/issues/206)) ([97deb51](https://github.com/ForestAdmin/agent-python/commit/97deb51fee304e56585e50e34ae5c056d79fc704))

## [1.6.1](https://github.com/ForestAdmin/agent-python/compare/v1.6.0...v1.6.1) (2024-03-22)


### Bug Fixes

* **usage:** allow string to be used next to enums ([#197](https://github.com/ForestAdmin/agent-python/issues/197)) ([1dee475](https://github.com/ForestAdmin/agent-python/commit/1dee47578da25a594a1a7e5dd46cdcdc4ccf8dbc))

# [1.6.0](https://github.com/ForestAdmin/agent-python/compare/v1.5.6...v1.6.0) (2024-03-22)


### Features

* call user function in correct context  ([#199](https://github.com/ForestAdmin/agent-python/issues/199)) ([a5308f4](https://github.com/ForestAdmin/agent-python/commit/a5308f4f619d1a588620951dabb3f905657bc7cb))

## [1.5.6](https://github.com/ForestAdmin/agent-python/compare/v1.5.5...v1.5.6) (2024-03-08)


### Bug Fixes

* **vulnerability:** replace python jose by pyjwt ([#193](https://github.com/ForestAdmin/agent-python/issues/193)) ([d7e0075](https://github.com/ForestAdmin/agent-python/commit/d7e00754937060427f62663f2ff4ab0a1c7d8b77))

## [1.5.5](https://github.com/ForestAdmin/agent-python/compare/v1.5.4...v1.5.5) (2024-03-06)


### Bug Fixes

* **uuid_field:** enable in and not in for uuid fields ([#192](https://github.com/ForestAdmin/agent-python/issues/192)) ([a77613b](https://github.com/ForestAdmin/agent-python/commit/a77613be4436197908a42afab6e2a4745ac6fa70))

## [1.5.4](https://github.com/ForestAdmin/agent-python/compare/v1.5.3...v1.5.4) (2024-02-29)


### Bug Fixes

* **tzdata_version:** remove dependencies to tzdata from packages ([#191](https://github.com/ForestAdmin/agent-python/issues/191)) ([2b17760](https://github.com/ForestAdmin/agent-python/commit/2b1776048233935a3035469b57cc1bd12041c2ad))

## [1.5.3](https://github.com/ForestAdmin/agent-python/compare/v1.5.2...v1.5.3) (2024-02-28)


### Bug Fixes

* **cache_invalidation:** wait more between each failed sse connection ([#189](https://github.com/ForestAdmin/agent-python/issues/189)) ([ec47651](https://github.com/ForestAdmin/agent-python/commit/ec476517747aad045a306f037d5384f135853e39))

## [1.5.2](https://github.com/ForestAdmin/agent-python/compare/v1.5.1...v1.5.2) (2024-02-15)


### Bug Fixes

* **security:** patch semantic-release dependency vulnerabilities ([#188](https://github.com/ForestAdmin/agent-python/issues/188)) ([87b8a6a](https://github.com/ForestAdmin/agent-python/commit/87b8a6afc96948f4e35f80fd26a4264f64b7243f))

## [1.5.1](https://github.com/ForestAdmin/agent-python/compare/v1.5.0...v1.5.1) (2024-02-08)


### Bug Fixes

* **schema:** force schema metadata update even in production ([#186](https://github.com/ForestAdmin/agent-python/issues/186)) ([f833e84](https://github.com/ForestAdmin/agent-python/commit/f833e845bd794460d3e474b642faef7be8a606de))

# [1.5.0](https://github.com/ForestAdmin/agent-python/compare/v1.4.0...v1.5.0) (2024-02-08)


### Features

* **action result builder:** allow user to set SA response headers ([#185](https://github.com/ForestAdmin/agent-python/issues/185)) ([0e98849](https://github.com/ForestAdmin/agent-python/commit/0e988493fdda67d34c703de0ae12e8eef0f1a9df))

# [1.4.0](https://github.com/ForestAdmin/agent-python/compare/v1.3.1...v1.4.0) (2024-02-06)


### Bug Fixes

* **csv:** export fails when there is more fields in data than projection ([#181](https://github.com/ForestAdmin/agent-python/issues/181)) ([2202877](https://github.com/ForestAdmin/agent-python/commit/2202877cd9bd4d22c84de5b0f4a76752c62d3a23))
* **datasource_django:** inexistant related object does not crash anymore ([#161](https://github.com/ForestAdmin/agent-python/issues/161)) ([53acaad](https://github.com/ForestAdmin/agent-python/commit/53acaad74a185e558c16480f455265588f3f9b78))
* **datasource_django:** proxy models are not added to datasource ([#158](https://github.com/ForestAdmin/agent-python/issues/158)) ([157e424](https://github.com/ForestAdmin/agent-python/commit/157e424b20587cf9805729c2b3ba6e4f6c83961f))
* **django:** allow requests during object serialization ([#178](https://github.com/ForestAdmin/agent-python/issues/178)) ([eb7dabf](https://github.com/ForestAdmin/agent-python/commit/eb7dabf014183dcf6eb04fc6229c76577406a581))
* **django_atomic_requests:** atomic requests can now be enabled ([#179](https://github.com/ForestAdmin/agent-python/issues/179)) ([3404165](https://github.com/ForestAdmin/agent-python/commit/34041654f0d62741f0a48a8e7314ed5177ac880a))
* **django_datasource:** django datasource now works when model fields use db_column ([#148](https://github.com/ForestAdmin/agent-python/issues/148)) ([4a99e8f](https://github.com/ForestAdmin/agent-python/commit/4a99e8f2cdb999041054a9215cff0ebbf23b9937))
* **django_introspection:** collection name is now the db table name ([#150](https://github.com/ForestAdmin/agent-python/issues/150)) ([8378c96](https://github.com/ForestAdmin/agent-python/commit/8378c96ff0a7e7eb1ecb2f3d37a74c1413fc9f85))
* **django_setup:** wait for all apps to be initialized before creating agent ([#169](https://github.com/ForestAdmin/agent-python/issues/169)) ([99bfaf1](https://github.com/ForestAdmin/agent-python/commit/99bfaf142f3fe2f3eb2bb3b4ae091e2034564efe))
* **enum:** force enums to be strings ([#175](https://github.com/ForestAdmin/agent-python/issues/175)) ([c3e546b](https://github.com/ForestAdmin/agent-python/commit/c3e546b8a1939fe1ebf81078b4a279d1165f53be))
* **enums:** handle not json serializable enum values ([#171](https://github.com/ForestAdmin/agent-python/issues/171)) ([537d25f](https://github.com/ForestAdmin/agent-python/commit/537d25ff5f53cbcd5f48963556faaf17df927be5))
* **float_serialization:** float number were serialized as int ([#180](https://github.com/ForestAdmin/agent-python/issues/180)) ([403e2e7](https://github.com/ForestAdmin/agent-python/commit/403e2e75ee42e7b8dc1ba89ae85893a4a617d175))
* **introspection:** editable attribute now determine is_readonly ([#168](https://github.com/ForestAdmin/agent-python/issues/168)) ([09db661](https://github.com/ForestAdmin/agent-python/commit/09db6619e5e53e9074479b10d5d758447f0158fd))
* **json_api:** correctly find id before retrieving related_url ([#162](https://github.com/ForestAdmin/agent-python/issues/162)) ([fa5738a](https://github.com/ForestAdmin/agent-python/commit/fa5738ae016c2bc12bfdc86d85b101466a643eb9))
* **polymorphic:** also ignore polymorphic reverse relations ([#172](https://github.com/ForestAdmin/agent-python/issues/172)) ([ba026cb](https://github.com/ForestAdmin/agent-python/commit/ba026cb8380846b354a3e03752afe9ae13db4a30))
* **relation:** introspection over self many to many works ([#170](https://github.com/ForestAdmin/agent-python/issues/170)) ([83dfdbb](https://github.com/ForestAdmin/agent-python/commit/83dfdbbeb6d5496885c2dc531f7da90dd9f5a91e))
* **time_only:** timeonly type was never validated ([#163](https://github.com/ForestAdmin/agent-python/issues/163)) ([4597bac](https://github.com/ForestAdmin/agent-python/commit/4597bac41016b8cab05a660d279ad34bcc174e24))
* foreign keys can be used as primary key ([#159](https://github.com/ForestAdmin/agent-python/issues/159)) ([5f18f73](https://github.com/ForestAdmin/agent-python/commit/5f18f73d1ab555dcd768a707fc88d432d0c43bd3))
* **relations:** gracefully ignore polymorphic relationships ([#157](https://github.com/ForestAdmin/agent-python/issues/157)) ([f1c2d6d](https://github.com/ForestAdmin/agent-python/commit/f1c2d6d06ea8e754059557d0c7640a142d6643b8))


### Features

* **django:** add database operations and routes ([#145](https://github.com/ForestAdmin/agent-python/issues/145)) ([95f3a94](https://github.com/ForestAdmin/agent-python/commit/95f3a94fc393ed1ea2d49849132717167c0961a7))
* **django_5:** support django 5 ([#164](https://github.com/ForestAdmin/agent-python/issues/164)) ([817db77](https://github.com/ForestAdmin/agent-python/commit/817db77e86f9aaab6e73a7352c586fdd032a86ba))
* **django_agent:** agent is ready to onboard on django project ([#147](https://github.com/ForestAdmin/agent-python/issues/147)) ([ac6135d](https://github.com/ForestAdmin/agent-python/commit/ac6135d905fd0cf1ed335d6a0c9eeba802ed2b43))
* **django_datasource:** add native driver ([#149](https://github.com/ForestAdmin/agent-python/issues/149)) ([5055031](https://github.com/ForestAdmin/agent-python/commit/5055031124d65f36bfd23d4adcdef72d40764eb8))
* **django_models_inheritance:** support django model inheritance ([#176](https://github.com/ForestAdmin/agent-python/issues/176)) ([6d27929](https://github.com/ForestAdmin/agent-python/commit/6d2792957778e9a43a5596cf3aa2368062759156))
* **search_hook:** add search hook route to django agent ([#183](https://github.com/ForestAdmin/agent-python/issues/183)) ([edbb1d1](https://github.com/ForestAdmin/agent-python/commit/edbb1d100605085d1290fa689c72bed4c13fea58))
* support python 3.12 ([#155](https://github.com/ForestAdmin/agent-python/issues/155)) ([93f8374](https://github.com/ForestAdmin/agent-python/commit/93f8374c204feda06bb7c3a78278caa138684fa5))

# [1.4.0-beta.2](https://github.com/ForestAdmin/agent-python/compare/v1.4.0-beta.1...v1.4.0-beta.2) (2024-02-05)


### Features

* **search_hook:** add search hook route to django agent ([#183](https://github.com/ForestAdmin/agent-python/issues/183)) ([edbb1d1](https://github.com/ForestAdmin/agent-python/commit/edbb1d100605085d1290fa689c72bed4c13fea58))

# [1.4.0-beta.1](https://github.com/ForestAdmin/agent-python/compare/v1.3.1...v1.4.0-beta.1) (2024-02-05)


### Bug Fixes

* **csv:** export fails when there is more fields in data than projection ([#181](https://github.com/ForestAdmin/agent-python/issues/181)) ([2202877](https://github.com/ForestAdmin/agent-python/commit/2202877cd9bd4d22c84de5b0f4a76752c62d3a23))
* **datasource_django:** inexistant related object does not crash anymore ([#161](https://github.com/ForestAdmin/agent-python/issues/161)) ([53acaad](https://github.com/ForestAdmin/agent-python/commit/53acaad74a185e558c16480f455265588f3f9b78))
* **datasource_django:** proxy models are not added to datasource ([#158](https://github.com/ForestAdmin/agent-python/issues/158)) ([157e424](https://github.com/ForestAdmin/agent-python/commit/157e424b20587cf9805729c2b3ba6e4f6c83961f))
* **django:** allow requests during object serialization ([#178](https://github.com/ForestAdmin/agent-python/issues/178)) ([eb7dabf](https://github.com/ForestAdmin/agent-python/commit/eb7dabf014183dcf6eb04fc6229c76577406a581))
* **django_atomic_requests:** atomic requests can now be enabled ([#179](https://github.com/ForestAdmin/agent-python/issues/179)) ([3404165](https://github.com/ForestAdmin/agent-python/commit/34041654f0d62741f0a48a8e7314ed5177ac880a))
* **django_datasource:** django datasource now works when model fields use db_column ([#148](https://github.com/ForestAdmin/agent-python/issues/148)) ([4a99e8f](https://github.com/ForestAdmin/agent-python/commit/4a99e8f2cdb999041054a9215cff0ebbf23b9937))
* **django_introspection:** collection name is now the db table name ([#150](https://github.com/ForestAdmin/agent-python/issues/150)) ([8378c96](https://github.com/ForestAdmin/agent-python/commit/8378c96ff0a7e7eb1ecb2f3d37a74c1413fc9f85))
* **django_setup:** wait for all apps to be initialized before creating agent ([#169](https://github.com/ForestAdmin/agent-python/issues/169)) ([99bfaf1](https://github.com/ForestAdmin/agent-python/commit/99bfaf142f3fe2f3eb2bb3b4ae091e2034564efe))
* **enum:** force enums to be strings ([#175](https://github.com/ForestAdmin/agent-python/issues/175)) ([c3e546b](https://github.com/ForestAdmin/agent-python/commit/c3e546b8a1939fe1ebf81078b4a279d1165f53be))
* **enums:** handle not json serializable enum values ([#171](https://github.com/ForestAdmin/agent-python/issues/171)) ([537d25f](https://github.com/ForestAdmin/agent-python/commit/537d25ff5f53cbcd5f48963556faaf17df927be5))
* **float_serialization:** float number were serialized as int ([#180](https://github.com/ForestAdmin/agent-python/issues/180)) ([403e2e7](https://github.com/ForestAdmin/agent-python/commit/403e2e75ee42e7b8dc1ba89ae85893a4a617d175))
* **introspection:** editable attribute now determine is_readonly ([#168](https://github.com/ForestAdmin/agent-python/issues/168)) ([09db661](https://github.com/ForestAdmin/agent-python/commit/09db6619e5e53e9074479b10d5d758447f0158fd))
* **json_api:** correctly find id before retrieving related_url ([#162](https://github.com/ForestAdmin/agent-python/issues/162)) ([fa5738a](https://github.com/ForestAdmin/agent-python/commit/fa5738ae016c2bc12bfdc86d85b101466a643eb9))
* **polymorphic:** also ignore polymorphic reverse relations ([#172](https://github.com/ForestAdmin/agent-python/issues/172)) ([ba026cb](https://github.com/ForestAdmin/agent-python/commit/ba026cb8380846b354a3e03752afe9ae13db4a30))
* **relation:** introspection over self many to many works ([#170](https://github.com/ForestAdmin/agent-python/issues/170)) ([83dfdbb](https://github.com/ForestAdmin/agent-python/commit/83dfdbbeb6d5496885c2dc531f7da90dd9f5a91e))
* **time_only:** timeonly type was never validated ([#163](https://github.com/ForestAdmin/agent-python/issues/163)) ([4597bac](https://github.com/ForestAdmin/agent-python/commit/4597bac41016b8cab05a660d279ad34bcc174e24))
* foreign keys can be used as primary key ([#159](https://github.com/ForestAdmin/agent-python/issues/159)) ([5f18f73](https://github.com/ForestAdmin/agent-python/commit/5f18f73d1ab555dcd768a707fc88d432d0c43bd3))
* **relations:** gracefully ignore polymorphic relationships ([#157](https://github.com/ForestAdmin/agent-python/issues/157)) ([f1c2d6d](https://github.com/ForestAdmin/agent-python/commit/f1c2d6d06ea8e754059557d0c7640a142d6643b8))


### Features

* **django:** add database operations and routes ([#145](https://github.com/ForestAdmin/agent-python/issues/145)) ([95f3a94](https://github.com/ForestAdmin/agent-python/commit/95f3a94fc393ed1ea2d49849132717167c0961a7))
* **django_5:** support django 5 ([#164](https://github.com/ForestAdmin/agent-python/issues/164)) ([817db77](https://github.com/ForestAdmin/agent-python/commit/817db77e86f9aaab6e73a7352c586fdd032a86ba))
* **django_agent:** agent is ready to onboard on django project ([#147](https://github.com/ForestAdmin/agent-python/issues/147)) ([ac6135d](https://github.com/ForestAdmin/agent-python/commit/ac6135d905fd0cf1ed335d6a0c9eeba802ed2b43))
* **django_datasource:** add native driver ([#149](https://github.com/ForestAdmin/agent-python/issues/149)) ([5055031](https://github.com/ForestAdmin/agent-python/commit/5055031124d65f36bfd23d4adcdef72d40764eb8))
* **django_models_inheritance:** support django model inheritance ([#176](https://github.com/ForestAdmin/agent-python/issues/176)) ([6d27929](https://github.com/ForestAdmin/agent-python/commit/6d2792957778e9a43a5596cf3aa2368062759156))
* support python 3.12 ([#155](https://github.com/ForestAdmin/agent-python/issues/155)) ([93f8374](https://github.com/ForestAdmin/agent-python/commit/93f8374c204feda06bb7c3a78278caa138684fa5))

# [1.3.0-beta.17](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.16...v1.3.0-beta.17) (2024-02-02)


### Bug Fixes

* **csv:** export fails when there is more fields in data than projection ([#181](https://github.com/ForestAdmin/agent-python/issues/181)) ([2202877](https://github.com/ForestAdmin/agent-python/commit/2202877cd9bd4d22c84de5b0f4a76752c62d3a23))

# [1.3.0-beta.16](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.15...v1.3.0-beta.16) (2024-02-01)


### Bug Fixes

* **float_serialization:** float number were serialized as int ([#180](https://github.com/ForestAdmin/agent-python/issues/180)) ([403e2e7](https://github.com/ForestAdmin/agent-python/commit/403e2e75ee42e7b8dc1ba89ae85893a4a617d175))

# [1.3.0-beta.15](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.14...v1.3.0-beta.15) (2024-02-01)


### Bug Fixes

* **django_atomic_requests:** atomic requests can now be enabled ([#179](https://github.com/ForestAdmin/agent-python/issues/179)) ([3404165](https://github.com/ForestAdmin/agent-python/commit/34041654f0d62741f0a48a8e7314ed5177ac880a))

# [1.3.0-beta.14](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.13...v1.3.0-beta.14) (2024-01-31)


### Bug Fixes

* **django:** allow requests during object serialization ([#178](https://github.com/ForestAdmin/agent-python/issues/178)) ([eb7dabf](https://github.com/ForestAdmin/agent-python/commit/eb7dabf014183dcf6eb04fc6229c76577406a581))

# [1.3.0-beta.13](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.12...v1.3.0-beta.13) (2024-01-29)


### Features

* **django_models_inheritance:** support django model inheritance ([#176](https://github.com/ForestAdmin/agent-python/issues/176)) ([6d27929](https://github.com/ForestAdmin/agent-python/commit/6d2792957778e9a43a5596cf3aa2368062759156))

# [1.3.0-beta.12](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.11...v1.3.0-beta.12) (2024-01-29)


### Bug Fixes

* **enum:** force enums to be strings ([#175](https://github.com/ForestAdmin/agent-python/issues/175)) ([c3e546b](https://github.com/ForestAdmin/agent-python/commit/c3e546b8a1939fe1ebf81078b4a279d1165f53be))

## [1.3.1](https://github.com/ForestAdmin/agent-python/compare/v1.3.0...v1.3.1) (2024-01-25)


### Bug Fixes

* **replace_field:** forbid null values on field replace functions ([#173](https://github.com/ForestAdmin/agent-python/issues/173)) ([d3de1b6](https://github.com/ForestAdmin/agent-python/commit/d3de1b6a3ed6984042d365de2f02e0146f372c6d))

# [1.3.0](https://github.com/ForestAdmin/agent-python/compare/v1.2.0...v1.3.0) (2024-01-24)


### Features

* **action_forms:** add widgets for smart action forms ([#165](https://github.com/ForestAdmin/agent-python/issues/165)) ([c6174f9](https://github.com/ForestAdmin/agent-python/commit/c6174f96a70cdeeaf1eb6450645d09891f307630))

# [1.3.0-beta.11](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.10...v1.3.0-beta.11) (2024-01-22)


### Bug Fixes

* **polymorphic:** also ignore polymorphic reverse relations ([#172](https://github.com/ForestAdmin/agent-python/issues/172)) ([ba026cb](https://github.com/ForestAdmin/agent-python/commit/ba026cb8380846b354a3e03752afe9ae13db4a30))

# [1.3.0-beta.10](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.9...v1.3.0-beta.10) (2024-01-22)


### Bug Fixes

* **relation:** introspection over self many to many works ([#170](https://github.com/ForestAdmin/agent-python/issues/170)) ([83dfdbb](https://github.com/ForestAdmin/agent-python/commit/83dfdbbeb6d5496885c2dc531f7da90dd9f5a91e))

# [1.3.0-beta.9](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.8...v1.3.0-beta.9) (2024-01-22)


### Bug Fixes

* **enums:** handle not json serializable enum values ([#171](https://github.com/ForestAdmin/agent-python/issues/171)) ([537d25f](https://github.com/ForestAdmin/agent-python/commit/537d25ff5f53cbcd5f48963556faaf17df927be5))

# [1.3.0-beta.8](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.7...v1.3.0-beta.8) (2024-01-17)


### Bug Fixes

* **django_setup:** wait for all apps to be initialized before creating agent ([#169](https://github.com/ForestAdmin/agent-python/issues/169)) ([99bfaf1](https://github.com/ForestAdmin/agent-python/commit/99bfaf142f3fe2f3eb2bb3b4ae091e2034564efe))

# [1.3.0-beta.7](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.6...v1.3.0-beta.7) (2024-01-17)


### Bug Fixes

* **introspection:** editable attribute now determine is_readonly ([#168](https://github.com/ForestAdmin/agent-python/issues/168)) ([09db661](https://github.com/ForestAdmin/agent-python/commit/09db6619e5e53e9074479b10d5d758447f0158fd))

# [1.3.0-beta.6](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.5...v1.3.0-beta.6) (2024-01-12)


### Features

* **django_5:** support django 5 ([#164](https://github.com/ForestAdmin/agent-python/issues/164)) ([817db77](https://github.com/ForestAdmin/agent-python/commit/817db77e86f9aaab6e73a7352c586fdd032a86ba))

# [1.3.0-beta.5](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.4...v1.3.0-beta.5) (2024-01-04)


### Bug Fixes

* **json_api:** correctly find id before retrieving related_url ([#162](https://github.com/ForestAdmin/agent-python/issues/162)) ([fa5738a](https://github.com/ForestAdmin/agent-python/commit/fa5738ae016c2bc12bfdc86d85b101466a643eb9))
* **time_only:** timeonly type was never validated ([#163](https://github.com/ForestAdmin/agent-python/issues/163)) ([4597bac](https://github.com/ForestAdmin/agent-python/commit/4597bac41016b8cab05a660d279ad34bcc174e24))

# [1.3.0-beta.4](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.3...v1.3.0-beta.4) (2024-01-02)


### Bug Fixes

* **datasource_django:** inexistant related object does not crash anymore ([#161](https://github.com/ForestAdmin/agent-python/issues/161)) ([53acaad](https://github.com/ForestAdmin/agent-python/commit/53acaad74a185e558c16480f455265588f3f9b78))

# [1.3.0-beta.3](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.2...v1.3.0-beta.3) (2023-12-27)


### Bug Fixes

* foreign keys can be used as primary key ([#159](https://github.com/ForestAdmin/agent-python/issues/159)) ([5f18f73](https://github.com/ForestAdmin/agent-python/commit/5f18f73d1ab555dcd768a707fc88d432d0c43bd3))

# [1.3.0-beta.2](https://github.com/ForestAdmin/agent-python/compare/v1.3.0-beta.1...v1.3.0-beta.2) (2023-12-20)


### Bug Fixes

* **datasource_django:** proxy models are not added to datasource ([#158](https://github.com/ForestAdmin/agent-python/issues/158)) ([157e424](https://github.com/ForestAdmin/agent-python/commit/157e424b20587cf9805729c2b3ba6e4f6c83961f))
* **relations:** gracefully ignore polymorphic relationships ([#157](https://github.com/ForestAdmin/agent-python/issues/157)) ([f1c2d6d](https://github.com/ForestAdmin/agent-python/commit/f1c2d6d06ea8e754059557d0c7640a142d6643b8))

# [1.3.0-beta.1](https://github.com/ForestAdmin/agent-python/compare/v1.2.0...v1.3.0-beta.1) (2023-12-19)


### Bug Fixes

* **django_datasource:** django datasource now works when model fields use db_column ([#148](https://github.com/ForestAdmin/agent-python/issues/148)) ([4a99e8f](https://github.com/ForestAdmin/agent-python/commit/4a99e8f2cdb999041054a9215cff0ebbf23b9937))
* **django_introspection:** collection name is now the db table name ([#150](https://github.com/ForestAdmin/agent-python/issues/150)) ([8378c96](https://github.com/ForestAdmin/agent-python/commit/8378c96ff0a7e7eb1ecb2f3d37a74c1413fc9f85))


### Features

* support python 3.12 ([#155](https://github.com/ForestAdmin/agent-python/issues/155)) ([93f8374](https://github.com/ForestAdmin/agent-python/commit/93f8374c204feda06bb7c3a78278caa138684fa5))
* **django:** add database operations and routes ([#145](https://github.com/ForestAdmin/agent-python/issues/145)) ([95f3a94](https://github.com/ForestAdmin/agent-python/commit/95f3a94fc393ed1ea2d49849132717167c0961a7))
* **django_agent:** agent is ready to onboard on django project ([#147](https://github.com/ForestAdmin/agent-python/issues/147)) ([ac6135d](https://github.com/ForestAdmin/agent-python/commit/ac6135d905fd0cf1ed335d6a0c9eeba802ed2b43))
* **django_datasource:** add native driver ([#149](https://github.com/ForestAdmin/agent-python/issues/149)) ([5055031](https://github.com/ForestAdmin/agent-python/commit/5055031124d65f36bfd23d4adcdef72d40764eb8))

# [1.2.0-beta.5](https://github.com/ForestAdmin/agent-python/compare/v1.2.0-beta.4...v1.2.0-beta.5) (2023-12-15)


### Features

* support python 3.12 ([#155](https://github.com/ForestAdmin/agent-python/issues/155)) ([93f8374](https://github.com/ForestAdmin/agent-python/commit/93f8374c204feda06bb7c3a78278caa138684fa5))

# [1.2.0](https://github.com/ForestAdmin/agent-python/compare/v1.1.4...v1.2.0) (2023-12-14)


### Features

* **python:** support of python 3.12 ([#153](https://github.com/ForestAdmin/agent-python/issues/153)) ([68e3b8d](https://github.com/ForestAdmin/agent-python/commit/68e3b8d19d40890b155637e12f4e08a25a2290d0))

# [1.2.0-beta.4](https://github.com/ForestAdmin/agent-python/compare/v1.2.0-beta.3...v1.2.0-beta.4) (2023-12-06)


### Bug Fixes

* **django_introspection:** collection name is now the db table name ([#150](https://github.com/ForestAdmin/agent-python/issues/150)) ([8378c96](https://github.com/ForestAdmin/agent-python/commit/8378c96ff0a7e7eb1ecb2f3d37a74c1413fc9f85))

## [1.1.4](https://github.com/ForestAdmin/agent-python/compare/v1.1.3...v1.1.4) (2023-12-06)


### Bug Fixes

* **csv_export:** csv export now exports data without applying pagination ([#152](https://github.com/ForestAdmin/agent-python/issues/152)) ([78f192c](https://github.com/ForestAdmin/agent-python/commit/78f192c1dd60ccd8c80dff3e333d1ca4f2abbc9f))

## [1.1.3](https://github.com/ForestAdmin/agent-python/compare/v1.1.2...v1.1.3) (2023-12-06)


### Bug Fixes

* **sse_thread:** framework autoreload now work when instant cache refresh is enabled ([#151](https://github.com/ForestAdmin/agent-python/issues/151)) ([1e980e8](https://github.com/ForestAdmin/agent-python/commit/1e980e8d16cec700d02c200bb3b290e9e1f0282a))

# [1.2.0-beta.3](https://github.com/ForestAdmin/agent-python/compare/v1.2.0-beta.2...v1.2.0-beta.3) (2023-12-01)


### Bug Fixes

* **django_datasource:** django datasource now works when model fields use db_column ([#148](https://github.com/ForestAdmin/agent-python/issues/148)) ([4a99e8f](https://github.com/ForestAdmin/agent-python/commit/4a99e8f2cdb999041054a9215cff0ebbf23b9937))


### Features

* **django_datasource:** add native driver ([#149](https://github.com/ForestAdmin/agent-python/issues/149)) ([5055031](https://github.com/ForestAdmin/agent-python/commit/5055031124d65f36bfd23d4adcdef72d40764eb8))

# [1.2.0-beta.2](https://github.com/ForestAdmin/agent-python/compare/v1.2.0-beta.1...v1.2.0-beta.2) (2023-11-28)


### Features

* **django_agent:** agent is ready to onboard on django project ([#147](https://github.com/ForestAdmin/agent-python/issues/147)) ([ac6135d](https://github.com/ForestAdmin/agent-python/commit/ac6135d905fd0cf1ed335d6a0c9eeba802ed2b43))

# [1.2.0-beta.1](https://github.com/ForestAdmin/agent-python/compare/v1.1.0...v1.2.0-beta.1) (2023-11-20)


### Features

* **django:** add database operations and routes ([#145](https://github.com/ForestAdmin/agent-python/issues/145)) ([95f3a94](https://github.com/ForestAdmin/agent-python/commit/95f3a94fc393ed1ea2d49849132717167c0961a7))

## [1.1.2](https://github.com/ForestAdmin/agent-python/compare/v1.1.1...v1.1.2) (2023-11-20)


### Bug Fixes

* **filter_emulation:** operator emulation now work on all primitive type ([#146](https://github.com/ForestAdmin/agent-python/issues/146)) ([aebc9df](https://github.com/ForestAdmin/agent-python/commit/aebc9df873817c8ea9af4738080db2f73d6a782a))

## [1.1.1](https://github.com/ForestAdmin/agent-python/compare/v1.1.0...v1.1.1) (2023-11-07)


### Bug Fixes

* **authentication:** return errors detail instead of generic error 500 ([#140](https://github.com/ForestAdmin/agent-python/issues/140)) ([0ac0510](https://github.com/ForestAdmin/agent-python/commit/0ac0510269925836f9a3f150db915b077570ec38))

# [1.1.0](https://github.com/ForestAdmin/agent-python/compare/v1.0.0...v1.1.0) (2023-10-31)


### Features

* **chart:** add multi line time based chart ([#139](https://github.com/ForestAdmin/agent-python/issues/139)) ([e918ade](https://github.com/ForestAdmin/agent-python/commit/e918adee9df3a0c1ffe90181de6bbdae663e1abc))

# 1.0.0 (2023-10-27)


### Bug Fixes

* **agent:** fix broken 1.0.0-beta.24 ([#126](https://github.com/ForestAdmin/agent-python/issues/126)) ([14f9d13](https://github.com/ForestAdmin/agent-python/commit/14f9d1305c6a0344f85927d3d9a586f83c7b4fa6))
* **agent_launching:** prevent the agent to be start multiple times ([#91](https://github.com/ForestAdmin/agent-python/issues/91)) ([b93cec1](https://github.com/ForestAdmin/agent-python/commit/b93cec1839781a4a66a417d9daeca60a3fdc0444))
* **caller:** add caller where it was missing ([#86](https://github.com/ForestAdmin/agent-python/issues/86)) ([8067617](https://github.com/ForestAdmin/agent-python/commit/8067617c7c25ebdb8ad994e37682f6b6cd4cc1d5))
* **condition_tree:** nested conditionTreeBranch are now recursively parsed ([#106](https://github.com/ForestAdmin/agent-python/issues/106)) ([427871f](https://github.com/ForestAdmin/agent-python/commit/427871ff82126a8bd7b534c89099c3582a40f0c7))
* **datasource:** create sqlalchmydatasource when using flask_sqlalchemy package ([#83](https://github.com/ForestAdmin/agent-python/issues/83)) ([caae7d0](https://github.com/ForestAdmin/agent-python/commit/caae7d059911e6621909f1793a6bf4e0c2299e04))
* **datasource-customizer:** add has_field_changed function to handle change hook on this field ([#113](https://github.com/ForestAdmin/agent-python/issues/113)) ([603c685](https://github.com/ForestAdmin/agent-python/commit/603c685f1a9ad2280a80b6708a66c394ca509fab))
* **export:** should return CSV with relationship fields ([#114](https://github.com/ForestAdmin/agent-python/issues/114)) ([1e396c7](https://github.com/ForestAdmin/agent-python/commit/1e396c71fd101caa04ae840689ac589a60385ac7))
* **filters:** use in operator with string type ([#122](https://github.com/ForestAdmin/agent-python/issues/122)) ([f2479e0](https://github.com/ForestAdmin/agent-python/commit/f2479e066e0b4a6449b4839dfa40793ee598bbd9))
* **json file:** handle json schema file on disk ([#67](https://github.com/ForestAdmin/agent-python/issues/67)) ([313993d](https://github.com/ForestAdmin/agent-python/commit/313993da39fc4657e974de9f29a4e12bb547a985))
* **json_api:** add href attribute into relationships ([#120](https://github.com/ForestAdmin/agent-python/issues/120)) ([476b8ad](https://github.com/ForestAdmin/agent-python/commit/476b8ad26759e522a39e54d2d4c3617f6ea67959))
* **logger:** file path and line number are now preserved ([#109](https://github.com/ForestAdmin/agent-python/issues/109)) ([b3b9064](https://github.com/ForestAdmin/agent-python/commit/b3b9064527428cb4c04e3726854c7a52f3ab04b1))
* **permissions:** permissions on related collection are now correctly checked ([#115](https://github.com/ForestAdmin/agent-python/issues/115)) ([99b750d](https://github.com/ForestAdmin/agent-python/commit/99b750d171d32a6468f1d12e0eaf7fb1c80c3df8))
* **python37:** fully compatible with python 3.7 ([#72](https://github.com/ForestAdmin/agent-python/issues/72)) ([71ee574](https://github.com/ForestAdmin/agent-python/commit/71ee5749eaddba5d1a42b3d5cab08118428b0279))
* **schema:** permit to use primary keys not named 'id' ([#112](https://github.com/ForestAdmin/agent-python/issues/112)) ([c3185be](https://github.com/ForestAdmin/agent-python/commit/c3185be31d61f3e0b076c7298ed20ca72e9ffb15))
* **search:** boolean filtering was broken ([#102](https://github.com/ForestAdmin/agent-python/issues/102)) ([164c7a2](https://github.com/ForestAdmin/agent-python/commit/164c7a262cd3cc0b9b304454c7c7ddaf84ca9b37))
* **search_metadata:** metadata of a search are now returned ([#111](https://github.com/ForestAdmin/agent-python/issues/111)) ([82b73e5](https://github.com/ForestAdmin/agent-python/commit/82b73e56cc3be5cc44cd856c735c8852a937d655))
* **setting:** prefix setting does not include forest suffix anymore ([#131](https://github.com/ForestAdmin/agent-python/issues/131)) ([a1ac3a9](https://github.com/ForestAdmin/agent-python/commit/a1ac3a9daf8479a2a66407a74e70bf743f35ba67))
* **sqlalchemy:** default_value on fields now works for schema generation ([#89](https://github.com/ForestAdmin/agent-python/issues/89)) ([f30b949](https://github.com/ForestAdmin/agent-python/commit/f30b94907f12ef0449b1284f6ef6e602747b0b4b))
* **sqlalchemy:** support more binary types, user defined types, columns aliases, and imperative model definition ([#135](https://github.com/ForestAdmin/agent-python/issues/135)) ([bb73f3b](https://github.com/ForestAdmin/agent-python/commit/bb73f3b20e2d5305ea5263bb8dfcac9b8ba07f4c))
* add some action test ([#60](https://github.com/ForestAdmin/agent-python/issues/60)) ([64f1ef6](https://github.com/ForestAdmin/agent-python/commit/64f1ef6c2245e2dd6657ab7e401057edfdfa237b))
* catchup nodejs bugfixes ([#118](https://github.com/ForestAdmin/agent-python/issues/118)) ([c14b89c](https://github.com/ForestAdmin/agent-python/commit/c14b89c4d18ec1eb6c0b160fa2458528d19d2764))
* **sqlalchemy:** not json serializable default value (auto now) set to null in schema ([#90](https://github.com/ForestAdmin/agent-python/issues/90)) ([de27104](https://github.com/ForestAdmin/agent-python/commit/de271042381be3d075ffef97839ab0ba81db26e6))
* **stats:** error on time chart time label parsing ([#107](https://github.com/ForestAdmin/agent-python/issues/107)) ([5f6cf39](https://github.com/ForestAdmin/agent-python/commit/5f6cf3931983ee610f0d3efcda7484d456aaf493))
* ci ([#20](https://github.com/ForestAdmin/agent-python/issues/20)) ([65b75ea](https://github.com/ForestAdmin/agent-python/commit/65b75ea8951ce7dd9bc9eeb95990b58d8d615d70))
* ci didn't update the flask agent poetry.lock ([1563426](https://github.com/ForestAdmin/agent-python/commit/1563426e2f08bac71c1a058ede75bb675c79effa))
* clean ci workflow ([24e79eb](https://github.com/ForestAdmin/agent-python/commit/24e79ebef226780973eeb8bb6be7625400e87bd1))
* current smart features was sometimes broken ([#64](https://github.com/ForestAdmin/agent-python/issues/64)) ([08ab362](https://github.com/ForestAdmin/agent-python/commit/08ab36261b32b7b3a1e0159af89d6a177c1f7fd2))
* extra async was missing for the flask dependency ([#55](https://github.com/ForestAdmin/agent-python/issues/55)) ([f4a9a01](https://github.com/ForestAdmin/agent-python/commit/f4a9a017d527ae661c6743e9c5e86bcec936a4c4))
* lock ci ([2bff2ea](https://github.com/ForestAdmin/agent-python/commit/2bff2ea1527ced45848db0b8de3e08556e7eec1f))
* lock ci ([62ed253](https://github.com/ForestAdmin/agent-python/commit/62ed253a310cf60dfe47db65050c5765f928ae8c))
* poetry lock action ([#61](https://github.com/ForestAdmin/agent-python/issues/61)) ([c507805](https://github.com/ForestAdmin/agent-python/commit/c507805404ad8565ee275a49aedd9411a9af8fa3))
* poetry lock ci ([#62](https://github.com/ForestAdmin/agent-python/issues/62)) ([489dabc](https://github.com/ForestAdmin/agent-python/commit/489dabc5a46e4fe5225651b7e599b49f04ce3346))
* remove circular import caused by a bad typing ([#48](https://github.com/ForestAdmin/agent-python/issues/48)) ([a91f9c7](https://github.com/ForestAdmin/agent-python/commit/a91f9c76afe815fc66f999043bc523a6f9bfb4d0))
* semantic release ci ([d23519a](https://github.com/ForestAdmin/agent-python/commit/d23519ab0e3feca9beb5a209fd3906647afcb3d3))
* semantic release ci ([#17](https://github.com/ForestAdmin/agent-python/issues/17)) ([fbb389e](https://github.com/ForestAdmin/agent-python/commit/fbb389ef355697fe03abd5562971c35e5137f6c9))
* semantic release ci ([#18](https://github.com/ForestAdmin/agent-python/issues/18)) ([245497b](https://github.com/ForestAdmin/agent-python/commit/245497b33cd2374c174a166e373f67770867ecb2))
* semantic release ci ([#19](https://github.com/ForestAdmin/agent-python/issues/19)) ([cdfe63d](https://github.com/ForestAdmin/agent-python/commit/cdfe63d9611bf1d80fe527d4296c6ee1a0be6fdc))
* semantic release workflow ([70f1bd5](https://github.com/ForestAdmin/agent-python/commit/70f1bd531dff9755b03890347971427aba5d198a))
* semantic release workflow ([#22](https://github.com/ForestAdmin/agent-python/issues/22)) ([a3de15a](https://github.com/ForestAdmin/agent-python/commit/a3de15a55552df219715ca82b94c1c1fc69285f5))
* semantic release workflow ([#53](https://github.com/ForestAdmin/agent-python/issues/53)) ([ac73506](https://github.com/ForestAdmin/agent-python/commit/ac735069f7004dd1e5af26f2440567c58ac6962c))
* the factory to build the complete projection for a collection was broken ([#63](https://github.com/ForestAdmin/agent-python/issues/63)) ([7444234](https://github.com/ForestAdmin/agent-python/commit/7444234f13f9fe32a6ab784135e643181ccb6a79))
* update the poetry.locks after the push to pypi in ci ([#58](https://github.com/ForestAdmin/agent-python/issues/58)) ([f460edf](https://github.com/ForestAdmin/agent-python/commit/f460edf279da88abb9d9628fecf500ced2db52cb))


### Features

* **actions:** add changed_field to ActionContext ([#99](https://github.com/ForestAdmin/agent-python/issues/99)) ([99d59dd](https://github.com/ForestAdmin/agent-python/commit/99d59dd1769a987d48020108c5b5ba6bf2a06c0b))
* **authentication:** agent_url parameter no longer needed ([#71](https://github.com/ForestAdmin/agent-python/issues/71)) ([be3632d](https://github.com/ForestAdmin/agent-python/commit/be3632d1f03b2fa53cbcdf7ab6500bf62589fd2c))
* **chart:** add chart decorator ([#92](https://github.com/ForestAdmin/agent-python/issues/92)) ([bb876da](https://github.com/ForestAdmin/agent-python/commit/bb876da273c65c6ab1e06f98ecaaf9ca79b6a0f2))
* **csv:** add csv export ([#79](https://github.com/ForestAdmin/agent-python/issues/79)) ([469ba79](https://github.com/ForestAdmin/agent-python/commit/469ba79463f478fc190c2fa4e885a37b519d3a7c))
* **customization:** add plugin system ([#123](https://github.com/ForestAdmin/agent-python/issues/123)) ([88a3b13](https://github.com/ForestAdmin/agent-python/commit/88a3b131ddf83f3c989e512478914ad9208b0309))
* **datasource:** add datasource customizer ([#68](https://github.com/ForestAdmin/agent-python/issues/68)) ([3001fb2](https://github.com/ForestAdmin/agent-python/commit/3001fb2b30a28324feadd481081cc7042d87f1a9))
* **decorator:** add binary decorator ([#129](https://github.com/ForestAdmin/agent-python/issues/129)) ([fb8f38c](https://github.com/ForestAdmin/agent-python/commit/fb8f38c0318f73f51ddb04577e66ee4e256534fa))
* **decorator:** add empty decorator ([#78](https://github.com/ForestAdmin/agent-python/issues/78)) ([6db3486](https://github.com/ForestAdmin/agent-python/commit/6db3486c2dbb7c4f2af2d17f1d9d1c2028ed7cba))
* **decorator:** add operator emulate decorator ([#97](https://github.com/ForestAdmin/agent-python/issues/97)) ([056b520](https://github.com/ForestAdmin/agent-python/commit/056b520392f55b68cac2cd86943acc8be241eac7))
* **decorator:** add schema decorator ([#85](https://github.com/ForestAdmin/agent-python/issues/85)) ([3cdb643](https://github.com/ForestAdmin/agent-python/commit/3cdb643a5d89a931b14c9b9eecb6e1ad3e533fca))
* **decorator:** add validation decorator ([#84](https://github.com/ForestAdmin/agent-python/issues/84)) ([0b2369f](https://github.com/ForestAdmin/agent-python/commit/0b2369f57df627a12243d5190934a79ef01c6132))
* **error_message:** add customize error message functionality ([#101](https://github.com/ForestAdmin/agent-python/issues/101)) ([62e8628](https://github.com/ForestAdmin/agent-python/commit/62e862814eb64d2846b2b64a4dc61fd60cb536bb))
* **hooks:** add hook decorator ([#104](https://github.com/ForestAdmin/agent-python/issues/104)) ([d6c75ee](https://github.com/ForestAdmin/agent-python/commit/d6c75ee4001b68c2feb3cf6468fa185dc8421677))
* **ip_whitelist:** add ip whitelist functionality ([#124](https://github.com/ForestAdmin/agent-python/issues/124)) ([9b06552](https://github.com/ForestAdmin/agent-python/commit/9b065522d0da26b82716fc78624bf45565fb5c52))
* **loggers:** add logger functionnality ([#100](https://github.com/ForestAdmin/agent-python/issues/100)) ([5d29726](https://github.com/ForestAdmin/agent-python/commit/5d29726f1c03df25d52eedc8279c4a812376552e))
* **native_driver:** add native driver ([#121](https://github.com/ForestAdmin/agent-python/issues/121)) ([c2b7a44](https://github.com/ForestAdmin/agent-python/commit/c2b7a44725f6125356b942a2527868311249b796))
* **permissions_v4:** add conditional approval, chart context variable ([#108](https://github.com/ForestAdmin/agent-python/issues/108)) ([afc49d6](https://github.com/ForestAdmin/agent-python/commit/afc49d63a4f6d9d470bd5fa48ae41b98377241f0))
* **publication:** add include, exclude and rename options to add_datasource   ([#117](https://github.com/ForestAdmin/agent-python/issues/117)) ([b191971](https://github.com/ForestAdmin/agent-python/commit/b191971b76089fdf53a3ce4007ea684af83f3a26))
* **relation:** add relation decorator ([#103](https://github.com/ForestAdmin/agent-python/issues/103)) ([c1f6859](https://github.com/ForestAdmin/agent-python/commit/c1f685978b0fc7194c0d42e145e4e894c30f8ec5))
* **semantic_release:** setting up semantic release ([#96](https://github.com/ForestAdmin/agent-python/issues/96)) ([f389ec0](https://github.com/ForestAdmin/agent-python/commit/f389ec0443913e127663678ceef321c21d429ba6))
* **settings:** add default settings to agent ([#66](https://github.com/ForestAdmin/agent-python/issues/66)) ([be60191](https://github.com/ForestAdmin/agent-python/commit/be601917c8ecc2d886e8bcfd826a3f282f8b2815))
* **settings:** agent settings are now integrated to flask settings ([#119](https://github.com/ForestAdmin/agent-python/issues/119)) ([3118669](https://github.com/ForestAdmin/agent-python/commit/31186691060cce623912f4b79f41db1b96f1ad74))
* **smart_actions:** smart actions can be defined using the classical forest api ([#116](https://github.com/ForestAdmin/agent-python/issues/116)) ([a2f80cb](https://github.com/ForestAdmin/agent-python/commit/a2f80cb6ee3975545cd9b9d77941824242c0d3f2))
* **sort_emulate:** add sort_emulate decorator ([#105](https://github.com/ForestAdmin/agent-python/issues/105)) ([73fef74](https://github.com/ForestAdmin/agent-python/commit/73fef74c0216561221de93bbfbafd916b46863fd))
* **write_decorator:** add field_writing decorator ([#94](https://github.com/ForestAdmin/agent-python/issues/94)) ([919c31d](https://github.com/ForestAdmin/agent-python/commit/919c31df7b5b916031d4d9299558965d1b7bf1fb))
* add caller support to collection calls ([#82](https://github.com/ForestAdmin/agent-python/issues/82)) ([e36e86e](https://github.com/ForestAdmin/agent-python/commit/e36e86e588966a9c12e8756a6dd96400fb0314a6))
* add decorator stack ([#87](https://github.com/ForestAdmin/agent-python/issues/87)) ([573ca7e](https://github.com/ForestAdmin/agent-python/commit/573ca7ea0d21e901c721189e03a34d224affb8b2))
* **sqlalchemy_datasource:** be compatible with flask_sqlalchemy integration ([#81](https://github.com/ForestAdmin/agent-python/issues/81)) ([7080129](https://github.com/ForestAdmin/agent-python/commit/708012940b0eab0af703e48acdd60780ca49cc94))
* add liana real metadata ([#77](https://github.com/ForestAdmin/agent-python/issues/77)) ([cd14cd4](https://github.com/ForestAdmin/agent-python/commit/cd14cd49708af6607e5324afb2a6561856a482ce))
* add the release action ([064b3f8](https://github.com/ForestAdmin/agent-python/commit/064b3f85c6971247ab703f23b401fd043d1de321))
* add the release action ([a80113a](https://github.com/ForestAdmin/agent-python/commit/a80113a2bae0ccd2f599819a27cf7fed4603d3e5))
* **stats:** add the stats resources ([b39763f](https://github.com/ForestAdmin/agent-python/commit/b39763f27745cdcaf721d3cd1a23fe46a57b2b79))
* flask-agent first alpha version ([6a0a644](https://github.com/ForestAdmin/agent-python/commit/6a0a644a587022cf38cd9836073835172c1ffb4b))
* flask-agent first alpha version ([c6e369c](https://github.com/ForestAdmin/agent-python/commit/c6e369c0949192aac052d61abcf498cadda23a14))

# [1.0.0-beta.30](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.29...v1.0.0-beta.30) (2023-10-26)


### Bug Fixes

* ci ([#20](https://github.com/ForestAdmin/agent-python/issues/20)) ([65b75ea](https://github.com/ForestAdmin/agent-python/commit/65b75ea8951ce7dd9bc9eeb95990b58d8d615d70))

# [1.0.0-beta.29](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.28...v1.0.0-beta.29) (2023-10-26)


### Bug Fixes

* **sqlalchemy:** support more binary types, user defined types, columns aliases, and imperative model definition ([#135](https://github.com/ForestAdmin/agent-python/issues/135)) ([bb73f3b](https://github.com/ForestAdmin/agent-python/commit/bb73f3b20e2d5305ea5263bb8dfcac9b8ba07f4c))

# [1.0.0-beta.28](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.27...v1.0.0-beta.28) (2023-10-24)


### Features

* **settings:** agent settings are now integrated to flask settings ([#119](https://github.com/ForestAdmin/agent-python/issues/119)) ([3118669](https://github.com/ForestAdmin/agent-python/commit/31186691060cce623912f4b79f41db1b96f1ad74))

# [1.0.0-beta.27](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.26...v1.0.0-beta.27) (2023-10-23)


### Bug Fixes

* **setting:** prefix setting does not include forest suffix anymore ([#131](https://github.com/ForestAdmin/agent-python/issues/131)) ([a1ac3a9](https://github.com/ForestAdmin/agent-python/commit/a1ac3a9daf8479a2a66407a74e70bf743f35ba67))

# [1.0.0-beta.26](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.25...v1.0.0-beta.26) (2023-10-17)


### Features

* **decorator:** add binary decorator ([#129](https://github.com/ForestAdmin/agent-python/issues/129)) ([fb8f38c](https://github.com/ForestAdmin/agent-python/commit/fb8f38c0318f73f51ddb04577e66ee4e256534fa))

# [1.0.0-beta.25](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.24...v1.0.0-beta.25) (2023-10-11)


### Bug Fixes

* **agent:** fix broken 1.0.0-beta.24 ([#126](https://github.com/ForestAdmin/agent-python/issues/126)) ([14f9d13](https://github.com/ForestAdmin/agent-python/commit/14f9d1305c6a0344f85927d3d9a586f83c7b4fa6))

# [1.0.0-beta.24](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.23...v1.0.0-beta.24) (2023-10-10)


### Features

* **ip_whitelist:** add ip whitelist functionality ([#124](https://github.com/ForestAdmin/agent-python/issues/124)) ([9b06552](https://github.com/ForestAdmin/agent-python/commit/9b065522d0da26b82716fc78624bf45565fb5c52))

# [1.0.0-beta.23](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.22...v1.0.0-beta.23) (2023-10-06)


### Features

* **customization:** add plugin system ([#123](https://github.com/ForestAdmin/agent-python/issues/123)) ([88a3b13](https://github.com/ForestAdmin/agent-python/commit/88a3b131ddf83f3c989e512478914ad9208b0309))

# [1.0.0-beta.22](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.21...v1.0.0-beta.22) (2023-10-04)


### Bug Fixes

* **json_api:** add href attribute into relationships ([#120](https://github.com/ForestAdmin/agent-python/issues/120)) ([476b8ad](https://github.com/ForestAdmin/agent-python/commit/476b8ad26759e522a39e54d2d4c3617f6ea67959))


### Features

* **native_driver:** add native driver ([#121](https://github.com/ForestAdmin/agent-python/issues/121)) ([c2b7a44](https://github.com/ForestAdmin/agent-python/commit/c2b7a44725f6125356b942a2527868311249b796))

# [1.0.0-beta.21](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.20...v1.0.0-beta.21) (2023-10-03)


### Bug Fixes

* **filters:** use in operator with string type ([#122](https://github.com/ForestAdmin/agent-python/issues/122)) ([f2479e0](https://github.com/ForestAdmin/agent-python/commit/f2479e066e0b4a6449b4839dfa40793ee598bbd9))

# [1.0.0-beta.20](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.19...v1.0.0-beta.20) (2023-09-28)


### Bug Fixes

* catchup nodejs bugfixes ([#118](https://github.com/ForestAdmin/agent-python/issues/118)) ([c14b89c](https://github.com/ForestAdmin/agent-python/commit/c14b89c4d18ec1eb6c0b160fa2458528d19d2764))

# [1.0.0-beta.19](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.18...v1.0.0-beta.19) (2023-09-28)


### Features

* **publication:** add include, exclude and rename options to add_datasource   ([#117](https://github.com/ForestAdmin/agent-python/issues/117)) ([b191971](https://github.com/ForestAdmin/agent-python/commit/b191971b76089fdf53a3ce4007ea684af83f3a26))

# [1.0.0-beta.18](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.17...v1.0.0-beta.18) (2023-09-19)


### Features

* **smart_actions:** smart actions can be defined using the classical forest api ([#116](https://github.com/ForestAdmin/agent-python/issues/116)) ([a2f80cb](https://github.com/ForestAdmin/agent-python/commit/a2f80cb6ee3975545cd9b9d77941824242c0d3f2))

# [1.0.0-beta.17](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.16...v1.0.0-beta.17) (2023-09-19)


### Bug Fixes

* **schema:** permit to use primary keys not named 'id' ([#112](https://github.com/ForestAdmin/agent-python/issues/112)) ([c3185be](https://github.com/ForestAdmin/agent-python/commit/c3185be31d61f3e0b076c7298ed20ca72e9ffb15))

# [1.0.0-beta.16](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.15...v1.0.0-beta.16) (2023-09-15)


### Bug Fixes

* **permissions:** permissions on related collection are now correctly checked ([#115](https://github.com/ForestAdmin/agent-python/issues/115)) ([99b750d](https://github.com/ForestAdmin/agent-python/commit/99b750d171d32a6468f1d12e0eaf7fb1c80c3df8))

# [1.0.0-beta.15](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.14...v1.0.0-beta.15) (2023-09-14)


### Bug Fixes

* **export:** should return CSV with relationship fields ([#114](https://github.com/ForestAdmin/agent-python/issues/114)) ([1e396c7](https://github.com/ForestAdmin/agent-python/commit/1e396c71fd101caa04ae840689ac589a60385ac7))

# [1.0.0-beta.14](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.13...v1.0.0-beta.14) (2023-09-14)


### Bug Fixes

* **datasource-customizer:** add has_field_changed function to handle change hook on this field ([#113](https://github.com/ForestAdmin/agent-python/issues/113)) ([603c685](https://github.com/ForestAdmin/agent-python/commit/603c685f1a9ad2280a80b6708a66c394ca509fab))

# [1.0.0-beta.13](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.12...v1.0.0-beta.13) (2023-09-13)


### Bug Fixes

* **search_metadata:** metadata of a search are now returned ([#111](https://github.com/ForestAdmin/agent-python/issues/111)) ([82b73e5](https://github.com/ForestAdmin/agent-python/commit/82b73e56cc3be5cc44cd856c735c8852a937d655))

# [1.0.0-beta.12](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.11...v1.0.0-beta.12) (2023-09-13)


### Bug Fixes

* **logger:** file path and line number are now preserved ([#109](https://github.com/ForestAdmin/agent-python/issues/109)) ([b3b9064](https://github.com/ForestAdmin/agent-python/commit/b3b9064527428cb4c04e3726854c7a52f3ab04b1))

# [1.0.0-beta.11](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.10...v1.0.0-beta.11) (2023-09-07)


### Features

* **permissions_v4:** add conditional approval, chart context variable ([#108](https://github.com/ForestAdmin/agent-python/issues/108)) ([afc49d6](https://github.com/ForestAdmin/agent-python/commit/afc49d63a4f6d9d470bd5fa48ae41b98377241f0))

# [1.0.0-beta.10](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.9...v1.0.0-beta.10) (2023-08-21)


### Bug Fixes

* **condition_tree:** nested conditionTreeBranch are now recursively parsed ([#106](https://github.com/ForestAdmin/agent-python/issues/106)) ([427871f](https://github.com/ForestAdmin/agent-python/commit/427871ff82126a8bd7b534c89099c3582a40f0c7))
* **stats:** error on time chart time label parsing ([#107](https://github.com/ForestAdmin/agent-python/issues/107)) ([5f6cf39](https://github.com/ForestAdmin/agent-python/commit/5f6cf3931983ee610f0d3efcda7484d456aaf493))

# [1.0.0-beta.9](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.8...v1.0.0-beta.9) (2023-08-17)


### Features

* **sort_emulate:** add sort_emulate decorator ([#105](https://github.com/ForestAdmin/agent-python/issues/105)) ([73fef74](https://github.com/ForestAdmin/agent-python/commit/73fef74c0216561221de93bbfbafd916b46863fd))

# [1.0.0-beta.8](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.7...v1.0.0-beta.8) (2023-08-10)


### Features

* **hooks:** add hook decorator ([#104](https://github.com/ForestAdmin/agent-python/issues/104)) ([d6c75ee](https://github.com/ForestAdmin/agent-python/commit/d6c75ee4001b68c2feb3cf6468fa185dc8421677))

# [1.0.0-beta.7](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.6...v1.0.0-beta.7) (2023-08-09)


### Features

* **relation:** add relation decorator ([#103](https://github.com/ForestAdmin/agent-python/issues/103)) ([c1f6859](https://github.com/ForestAdmin/agent-python/commit/c1f685978b0fc7194c0d42e145e4e894c30f8ec5))

# [1.0.0-beta.6](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.5...v1.0.0-beta.6) (2023-08-08)


### Bug Fixes

* **search:** boolean filtering was broken ([#102](https://github.com/ForestAdmin/agent-python/issues/102)) ([164c7a2](https://github.com/ForestAdmin/agent-python/commit/164c7a262cd3cc0b9b304454c7c7ddaf84ca9b37))

# [1.0.0-beta.5](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.4...v1.0.0-beta.5) (2023-08-01)


### Features

* **error_message:** add customize error message functionality ([#101](https://github.com/ForestAdmin/agent-python/issues/101)) ([62e8628](https://github.com/ForestAdmin/agent-python/commit/62e862814eb64d2846b2b64a4dc61fd60cb536bb))

# [1.0.0-beta.4](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.3...v1.0.0-beta.4) (2023-07-31)


### Features

* **loggers:** add logger functionnality ([#100](https://github.com/ForestAdmin/agent-python/issues/100)) ([5d29726](https://github.com/ForestAdmin/agent-python/commit/5d29726f1c03df25d52eedc8279c4a812376552e))

# [1.0.0-beta.3](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.2...v1.0.0-beta.3) (2023-07-27)


### Features

* **actions:** add changed_field to ActionContext ([#99](https://github.com/ForestAdmin/agent-python/issues/99)) ([99d59dd](https://github.com/ForestAdmin/agent-python/commit/99d59dd1769a987d48020108c5b5ba6bf2a06c0b))

# [1.0.0-beta.2](https://github.com/ForestAdmin/agent-python/compare/v1.0.0-beta.1...v1.0.0-beta.2) (2023-07-26)


### Features

* **decorator:** add operator emulate decorator ([#97](https://github.com/ForestAdmin/agent-python/issues/97)) ([056b520](https://github.com/ForestAdmin/agent-python/commit/056b520392f55b68cac2cd86943acc8be241eac7))

# 1.0.0-beta.1 (2023-07-21)


### Bug Fixes

* **agent_launching:** prevent the agent to be start multiple times ([#91](https://github.com/ForestAdmin/agent-python/issues/91)) ([b93cec1](https://github.com/ForestAdmin/agent-python/commit/b93cec1839781a4a66a417d9daeca60a3fdc0444))
* **caller:** add caller where it was missing ([#86](https://github.com/ForestAdmin/agent-python/issues/86)) ([8067617](https://github.com/ForestAdmin/agent-python/commit/8067617c7c25ebdb8ad994e37682f6b6cd4cc1d5))
* **datasource:** create sqlalchmydatasource when using flask_sqlalchemy package ([#83](https://github.com/ForestAdmin/agent-python/issues/83)) ([caae7d0](https://github.com/ForestAdmin/agent-python/commit/caae7d059911e6621909f1793a6bf4e0c2299e04))
* **json file:** handle json schema file on disk ([#67](https://github.com/ForestAdmin/agent-python/issues/67)) ([313993d](https://github.com/ForestAdmin/agent-python/commit/313993da39fc4657e974de9f29a4e12bb547a985))
* **python37:** fully compatible with python 3.7 ([#72](https://github.com/ForestAdmin/agent-python/issues/72)) ([71ee574](https://github.com/ForestAdmin/agent-python/commit/71ee5749eaddba5d1a42b3d5cab08118428b0279))
* **sqlalchemy:** default_value on fields now works for schema generation ([#89](https://github.com/ForestAdmin/agent-python/issues/89)) ([f30b949](https://github.com/ForestAdmin/agent-python/commit/f30b94907f12ef0449b1284f6ef6e602747b0b4b))
* **sqlalchemy:** not json serializable default value (auto now) set to null in schema ([#90](https://github.com/ForestAdmin/agent-python/issues/90)) ([de27104](https://github.com/ForestAdmin/agent-python/commit/de271042381be3d075ffef97839ab0ba81db26e6))
* add some action test ([#60](https://github.com/ForestAdmin/agent-python/issues/60)) ([64f1ef6](https://github.com/ForestAdmin/agent-python/commit/64f1ef6c2245e2dd6657ab7e401057edfdfa237b))
* ci didn't update the flask agent poetry.lock ([1563426](https://github.com/ForestAdmin/agent-python/commit/1563426e2f08bac71c1a058ede75bb675c79effa))
* clean ci workflow ([24e79eb](https://github.com/ForestAdmin/agent-python/commit/24e79ebef226780973eeb8bb6be7625400e87bd1))
* current smart features was sometimes broken ([#64](https://github.com/ForestAdmin/agent-python/issues/64)) ([08ab362](https://github.com/ForestAdmin/agent-python/commit/08ab36261b32b7b3a1e0159af89d6a177c1f7fd2))
* extra async was missing for the flask dependency ([#55](https://github.com/ForestAdmin/agent-python/issues/55)) ([f4a9a01](https://github.com/ForestAdmin/agent-python/commit/f4a9a017d527ae661c6743e9c5e86bcec936a4c4))
* lock ci ([2bff2ea](https://github.com/ForestAdmin/agent-python/commit/2bff2ea1527ced45848db0b8de3e08556e7eec1f))
* lock ci ([62ed253](https://github.com/ForestAdmin/agent-python/commit/62ed253a310cf60dfe47db65050c5765f928ae8c))
* poetry lock action ([#61](https://github.com/ForestAdmin/agent-python/issues/61)) ([c507805](https://github.com/ForestAdmin/agent-python/commit/c507805404ad8565ee275a49aedd9411a9af8fa3))
* poetry lock ci ([#62](https://github.com/ForestAdmin/agent-python/issues/62)) ([489dabc](https://github.com/ForestAdmin/agent-python/commit/489dabc5a46e4fe5225651b7e599b49f04ce3346))
* remove circular import caused by a bad typing ([#48](https://github.com/ForestAdmin/agent-python/issues/48)) ([a91f9c7](https://github.com/ForestAdmin/agent-python/commit/a91f9c76afe815fc66f999043bc523a6f9bfb4d0))
* semantic release ci ([d23519a](https://github.com/ForestAdmin/agent-python/commit/d23519ab0e3feca9beb5a209fd3906647afcb3d3))
* semantic release ci ([#17](https://github.com/ForestAdmin/agent-python/issues/17)) ([fbb389e](https://github.com/ForestAdmin/agent-python/commit/fbb389ef355697fe03abd5562971c35e5137f6c9))
* semantic release ci ([#18](https://github.com/ForestAdmin/agent-python/issues/18)) ([245497b](https://github.com/ForestAdmin/agent-python/commit/245497b33cd2374c174a166e373f67770867ecb2))
* semantic release ci ([#19](https://github.com/ForestAdmin/agent-python/issues/19)) ([cdfe63d](https://github.com/ForestAdmin/agent-python/commit/cdfe63d9611bf1d80fe527d4296c6ee1a0be6fdc))
* semantic release workflow ([70f1bd5](https://github.com/ForestAdmin/agent-python/commit/70f1bd531dff9755b03890347971427aba5d198a))
* semantic release workflow ([#22](https://github.com/ForestAdmin/agent-python/issues/22)) ([a3de15a](https://github.com/ForestAdmin/agent-python/commit/a3de15a55552df219715ca82b94c1c1fc69285f5))
* semantic release workflow ([#53](https://github.com/ForestAdmin/agent-python/issues/53)) ([ac73506](https://github.com/ForestAdmin/agent-python/commit/ac735069f7004dd1e5af26f2440567c58ac6962c))
* the factory to build the complete projection for a collection was broken ([#63](https://github.com/ForestAdmin/agent-python/issues/63)) ([7444234](https://github.com/ForestAdmin/agent-python/commit/7444234f13f9fe32a6ab784135e643181ccb6a79))
* update the poetry.locks after the push to pypi in ci ([#58](https://github.com/ForestAdmin/agent-python/issues/58)) ([f460edf](https://github.com/ForestAdmin/agent-python/commit/f460edf279da88abb9d9628fecf500ced2db52cb))


### Features

* **authentication:** agent_url parameter no longer needed ([#71](https://github.com/ForestAdmin/agent-python/issues/71)) ([be3632d](https://github.com/ForestAdmin/agent-python/commit/be3632d1f03b2fa53cbcdf7ab6500bf62589fd2c))
* **chart:** add chart decorator ([#92](https://github.com/ForestAdmin/agent-python/issues/92)) ([bb876da](https://github.com/ForestAdmin/agent-python/commit/bb876da273c65c6ab1e06f98ecaaf9ca79b6a0f2))
* **csv:** add csv export ([#79](https://github.com/ForestAdmin/agent-python/issues/79)) ([469ba79](https://github.com/ForestAdmin/agent-python/commit/469ba79463f478fc190c2fa4e885a37b519d3a7c))
* **datasource:** add datasource customizer ([#68](https://github.com/ForestAdmin/agent-python/issues/68)) ([3001fb2](https://github.com/ForestAdmin/agent-python/commit/3001fb2b30a28324feadd481081cc7042d87f1a9))
* **decorator:** add empty decorator ([#78](https://github.com/ForestAdmin/agent-python/issues/78)) ([6db3486](https://github.com/ForestAdmin/agent-python/commit/6db3486c2dbb7c4f2af2d17f1d9d1c2028ed7cba))
* **decorator:** add schema decorator ([#85](https://github.com/ForestAdmin/agent-python/issues/85)) ([3cdb643](https://github.com/ForestAdmin/agent-python/commit/3cdb643a5d89a931b14c9b9eecb6e1ad3e533fca))
* **decorator:** add validation decorator ([#84](https://github.com/ForestAdmin/agent-python/issues/84)) ([0b2369f](https://github.com/ForestAdmin/agent-python/commit/0b2369f57df627a12243d5190934a79ef01c6132))
* **semantic_release:** setting up semantic release ([#96](https://github.com/ForestAdmin/agent-python/issues/96)) ([f389ec0](https://github.com/ForestAdmin/agent-python/commit/f389ec0443913e127663678ceef321c21d429ba6))
* **stats:** add the stats resources ([b39763f](https://github.com/ForestAdmin/agent-python/commit/b39763f27745cdcaf721d3cd1a23fe46a57b2b79))
* **write_decorator:** add field_writing decorator ([#94](https://github.com/ForestAdmin/agent-python/issues/94)) ([919c31d](https://github.com/ForestAdmin/agent-python/commit/919c31df7b5b916031d4d9299558965d1b7bf1fb))
* add caller support to collection calls ([#82](https://github.com/ForestAdmin/agent-python/issues/82)) ([e36e86e](https://github.com/ForestAdmin/agent-python/commit/e36e86e588966a9c12e8756a6dd96400fb0314a6))
* add decorator stack ([#87](https://github.com/ForestAdmin/agent-python/issues/87)) ([573ca7e](https://github.com/ForestAdmin/agent-python/commit/573ca7ea0d21e901c721189e03a34d224affb8b2))
* **sqlalchemy_datasource:** be compatible with flask_sqlalchemy integration ([#81](https://github.com/ForestAdmin/agent-python/issues/81)) ([7080129](https://github.com/ForestAdmin/agent-python/commit/708012940b0eab0af703e48acdd60780ca49cc94))
* add liana real metadata ([#77](https://github.com/ForestAdmin/agent-python/issues/77)) ([cd14cd4](https://github.com/ForestAdmin/agent-python/commit/cd14cd49708af6607e5324afb2a6561856a482ce))
* **settings:** add default settings to agent ([#66](https://github.com/ForestAdmin/agent-python/issues/66)) ([be60191](https://github.com/ForestAdmin/agent-python/commit/be601917c8ecc2d886e8bcfd826a3f282f8b2815))
* add the release action ([064b3f8](https://github.com/ForestAdmin/agent-python/commit/064b3f85c6971247ab703f23b401fd043d1de321))
* add the release action ([a80113a](https://github.com/ForestAdmin/agent-python/commit/a80113a2bae0ccd2f599819a27cf7fed4603d3e5))
* flask-agent first alpha version ([6a0a644](https://github.com/ForestAdmin/agent-python/commit/6a0a644a587022cf38cd9836073835172c1ffb4b))
* flask-agent first alpha version ([c6e369c](https://github.com/ForestAdmin/agent-python/commit/c6e369c0949192aac052d61abcf498cadda23a14))

# Changelog

<!--next-version-placeholder-->

## v0.1.0-beta.43 (2023-07-13)



## v0.1.0-beta.42 (2023-07-12)

### Feature

* **chart:** Add chart decorator ([#92](https://github.com/ForestAdmin/agent-python/issues/92)) ([`bb876da`](https://github.com/ForestAdmin/agent-python/commit/bb876da273c65c6ab1e06f98ecaaf9ca79b6a0f2))

## v0.1.0-beta.41 (2023-07-11)

### Fix

* **agent_launching:** Prevent the agent to be start multiple times ([#91](https://github.com/ForestAdmin/agent-python/issues/91)) ([`b93cec1`](https://github.com/ForestAdmin/agent-python/commit/b93cec1839781a4a66a417d9daeca60a3fdc0444))

## v0.1.0-beta.40 (2023-07-10)

### Fix

* **sqlalchemy:** Not json serializable default value (auto now) set to null in schema ([#90](https://github.com/ForestAdmin/agent-python/issues/90)) ([`de27104`](https://github.com/ForestAdmin/agent-python/commit/de271042381be3d075ffef97839ab0ba81db26e6))

## v0.1.0-beta.39 (2023-07-10)

### Fix

* **sqlalchemy:** Default_value on fields now works for schema generation ([#89](https://github.com/ForestAdmin/agent-python/issues/89)) ([`f30b949`](https://github.com/ForestAdmin/agent-python/commit/f30b94907f12ef0449b1284f6ef6e602747b0b4b))

## v0.1.0-beta.38 (2023-07-05)



## v0.1.0-beta.37 (2023-06-28)

### Fix

* **datasource:** Create sqlalchmydatasource when using flask_sqlalchemy package ([#83](https://github.com/ForestAdmin/agent-python/issues/83)) ([`caae7d0`](https://github.com/ForestAdmin/agent-python/commit/caae7d059911e6621909f1793a6bf4e0c2299e04))

## v0.1.0-beta.36 (2023-06-28)

### Feature

* Add decorator stack ([#87](https://github.com/ForestAdmin/agent-python/issues/87)) ([`573ca7e`](https://github.com/ForestAdmin/agent-python/commit/573ca7ea0d21e901c721189e03a34d224affb8b2))

## v0.1.0-beta.35 (2023-06-19)

### Fix

* **caller:** Add caller where it was missing ([#86](https://github.com/ForestAdmin/agent-python/issues/86)) ([`8067617`](https://github.com/ForestAdmin/agent-python/commit/8067617c7c25ebdb8ad994e37682f6b6cd4cc1d5))

## v0.1.0-beta.34 (2023-06-15)

### Feature

* **decorator:** Add schema decorator ([#85](https://github.com/ForestAdmin/agent-python/issues/85)) ([`3cdb643`](https://github.com/ForestAdmin/agent-python/commit/3cdb643a5d89a931b14c9b9eecb6e1ad3e533fca))

## v0.1.0-beta.33 (2023-06-15)

### Feature

* **decorator:** Add validation decorator ([#84](https://github.com/ForestAdmin/agent-python/issues/84)) ([`0b2369f`](https://github.com/ForestAdmin/agent-python/commit/0b2369f57df627a12243d5190934a79ef01c6132))

## v0.1.0-beta.32 (2023-06-12)

### Feature

* Add caller support to collection calls ([#82](https://github.com/ForestAdmin/agent-python/issues/82)) ([`e36e86e`](https://github.com/ForestAdmin/agent-python/commit/e36e86e588966a9c12e8756a6dd96400fb0314a6))

## v0.1.0-beta.31 (2023-06-12)

### Feature

* **sqlalchemy_datasource:** Be compatible with flask_sqlalchemy integration ([#81](https://github.com/ForestAdmin/agent-python/issues/81)) ([`7080129`](https://github.com/ForestAdmin/agent-python/commit/708012940b0eab0af703e48acdd60780ca49cc94))

## v0.1.0-beta.30 (2023-06-08)

### Feature

* **csv:** Add csv export ([#79](https://github.com/ForestAdmin/agent-python/issues/79)) ([`469ba79`](https://github.com/ForestAdmin/agent-python/commit/469ba79463f478fc190c2fa4e885a37b519d3a7c))

## v0.1.0-beta.29 (2023-06-01)


## v0.1.0-beta.28 (2023-05-29)
### Feature

* **decorator:** Add empty decorator ([#78](https://github.com/ForestAdmin/agent-python/issues/78)) ([`6db3486`](https://github.com/ForestAdmin/agent-python/commit/6db3486c2dbb7c4f2af2d17f1d9d1c2028ed7cba))

## v0.1.0-beta.27 (2023-05-26)


## v0.1.0-beta.26 (2023-05-25)
### Feature
* Add liana real metadata ([#77](https://github.com/ForestAdmin/agent-python/issues/77)) ([`cd14cd4`](https://github.com/ForestAdmin/agent-python/commit/cd14cd49708af6607e5324afb2a6561856a482ce))

## v0.1.0-beta.25 (2023-05-25)


## v0.1.0-beta.24 (2023-05-23)


## v0.1.0-beta.23 (2023-05-15)


## v0.1.0-beta.22 (2023-05-11)
### Fix
* **python37:** Fully compatible with python 3.7 ([#72](https://github.com/ForestAdmin/agent-python/issues/72)) ([`71ee574`](https://github.com/ForestAdmin/agent-python/commit/71ee5749eaddba5d1a42b3d5cab08118428b0279))

## v0.1.0-beta.21 (2023-05-11)
### Feature
* **authentication:** Agent_url parameter no longer needed ([#71](https://github.com/ForestAdmin/agent-python/issues/71)) ([`be3632d`](https://github.com/ForestAdmin/agent-python/commit/be3632d1f03b2fa53cbcdf7ab6500bf62589fd2c))

## v0.1.0-beta.20 (2023-05-10)


## v0.1.0-beta.19 (2023-05-02)
### Feature
* **datasource:** Add datasource customizer ([#68](https://github.com/ForestAdmin/agent-python/issues/68)) ([`3001fb2`](https://github.com/ForestAdmin/agent-python/commit/3001fb2b30a28324feadd481081cc7042d87f1a9))

## v0.1.0-beta.18 (2023-04-25)
### Fix
* **json file:** Handle json schema file on disk ([#67](https://github.com/ForestAdmin/agent-python/issues/67)) ([`313993d`](https://github.com/ForestAdmin/agent-python/commit/313993da39fc4657e974de9f29a4e12bb547a985))

## v0.1.0-beta.17 (2023-04-20)
### Feature
* **settings:** Add default settings to agent ([#66](https://github.com/ForestAdmin/agent-python/issues/66)) ([`be60191`](https://github.com/ForestAdmin/agent-python/commit/be601917c8ecc2d886e8bcfd826a3f282f8b2815))

## v0.1.0-beta.16 (2022-12-14)


## v0.1.0-beta.15 (2022-12-14)
### Fix
* Ci didn't update the flask agent poetry.lock ([`1563426`](https://github.com/ForestAdmin/agent-python/commit/1563426e2f08bac71c1a058ede75bb675c79effa))

## v0.1.0-beta.14 (2022-12-14)
### Fix
* Current smart features was sometimes broken ([#64](https://github.com/ForestAdmin/agent-python/issues/64)) ([`08ab362`](https://github.com/ForestAdmin/agent-python/commit/08ab36261b32b7b3a1e0159af89d6a177c1f7fd2))

## v0.1.0-beta.13 (2022-12-08)
### Fix
* The factory to build the complete projection for a collection was broken ([#63](https://github.com/ForestAdmin/agent-python/issues/63)) ([`7444234`](https://github.com/ForestAdmin/agent-python/commit/7444234f13f9fe32a6ab784135e643181ccb6a79))

## v0.1.0-beta.12 (2022-12-07)
### Fix
* Extra async was missing for the flask dependency ([#55](https://github.com/ForestAdmin/agent-python/issues/55)) ([`f4a9a01`](https://github.com/ForestAdmin/agent-python/commit/f4a9a017d527ae661c6743e9c5e86bcec936a4c4))

## v0.1.0-beta.11 (2022-12-07)
### Fix
* Clean ci workflow ([`24e79eb`](https://github.com/ForestAdmin/agent-python/commit/24e79ebef226780973eeb8bb6be7625400e87bd1))

## v0.1.0-beta.10 (2022-12-07)
### Fix
* Lock ci ([`2bff2ea`](https://github.com/ForestAdmin/agent-python/commit/2bff2ea1527ced45848db0b8de3e08556e7eec1f))

## v0.1.0-beta.9 (2022-12-07)
### Fix
* Lock ci ([`62ed253`](https://github.com/ForestAdmin/agent-python/commit/62ed253a310cf60dfe47db65050c5765f928ae8c))

## v0.1.0-beta.8 (2022-12-07)
### Fix
* Poetry lock ci ([#62](https://github.com/ForestAdmin/agent-python/issues/62)) ([`489dabc`](https://github.com/ForestAdmin/agent-python/commit/489dabc5a46e4fe5225651b7e599b49f04ce3346))

## v0.1.0-beta.7 (2022-12-07)
### Fix
* Poetry lock action ([#61](https://github.com/ForestAdmin/agent-python/issues/61)) ([`c507805`](https://github.com/ForestAdmin/agent-python/commit/c507805404ad8565ee275a49aedd9411a9af8fa3))

## v0.1.0-beta.6 (2022-12-07)
### Fix
* Add some action test ([#60](https://github.com/ForestAdmin/agent-python/issues/60)) ([`64f1ef6`](https://github.com/ForestAdmin/agent-python/commit/64f1ef6c2245e2dd6657ab7e401057edfdfa237b))

## v0.1.0-beta.5 (2022-12-07)
### Fix
* Update the poetry.locks after the push to pypi in ci ([#58](https://github.com/ForestAdmin/agent-python/issues/58)) ([`f460edf`](https://github.com/ForestAdmin/agent-python/commit/f460edf279da88abb9d9628fecf500ced2db52cb))

## v0.1.0-beta.4 (2022-12-07)


## v0.1.0-beta.3 (2022-12-06)


## v0.1.0-beta.2 (2022-12-06)
### Fix
* Remove circular import caused by a bad typing ([#48](https://github.com/ForestAdmin/agent-python/issues/48)) ([`a91f9c7`](https://github.com/ForestAdmin/agent-python/commit/a91f9c76afe815fc66f999043bc523a6f9bfb4d0))

## v0.1.0-beta.1 (2022-12-06)
### Feature
* Add the release action ([`064b3f8`](https://github.com/ForestAdmin/agent-python/commit/064b3f85c6971247ab703f23b401fd043d1de321))
* Add the release action ([`a80113a`](https://github.com/ForestAdmin/agent-python/commit/a80113a2bae0ccd2f599819a27cf7fed4603d3e5))
* **stats:** Add the stats resources ([`b39763f`](https://github.com/ForestAdmin/agent-python/commit/b39763f27745cdcaf721d3cd1a23fe46a57b2b79))
* Flask-agent first alpha version ([`6a0a644`](https://github.com/ForestAdmin/agent-python/commit/6a0a644a587022cf38cd9836073835172c1ffb4b))
* Flask-agent first alpha version ([`c6e369c`](https://github.com/ForestAdmin/agent-python/commit/c6e369c0949192aac052d61abcf498cadda23a14))

### Fix
* Semantic release workflow ([#53](https://github.com/ForestAdmin/agent-python/issues/53)) ([`ac73506`](https://github.com/ForestAdmin/agent-python/commit/ac735069f7004dd1e5af26f2440567c58ac6962c))
* Semantic release workflow ([#22](https://github.com/ForestAdmin/agent-python/issues/22)) ([`a3de15a`](https://github.com/ForestAdmin/agent-python/commit/a3de15a55552df219715ca82b94c1c1fc69285f5))
* Semantic release workflow ([`70f1bd5`](https://github.com/ForestAdmin/agent-python/commit/70f1bd531dff9755b03890347971427aba5d198a))
* Semantic release ci ([#19](https://github.com/ForestAdmin/agent-python/issues/19)) ([`cdfe63d`](https://github.com/ForestAdmin/agent-python/commit/cdfe63d9611bf1d80fe527d4296c6ee1a0be6fdc))
* Semantic release ci ([#18](https://github.com/ForestAdmin/agent-python/issues/18)) ([`245497b`](https://github.com/ForestAdmin/agent-python/commit/245497b33cd2374c174a166e373f67770867ecb2))
* Semantic release ci ([#17](https://github.com/ForestAdmin/agent-python/issues/17)) ([`fbb389e`](https://github.com/ForestAdmin/agent-python/commit/fbb389ef355697fe03abd5562971c35e5137f6c9))
* Semantic release ci ([`d23519a`](https://github.com/ForestAdmin/agent-python/commit/d23519ab0e3feca9beb5a209fd3906647afcb3d3))
