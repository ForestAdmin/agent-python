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
