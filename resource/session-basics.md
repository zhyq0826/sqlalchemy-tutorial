# Session Basics

## What does the Session do ?

In the most general sense, the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) establishes all conversations with the database and represents a “holding zone” for all the objects which you’ve loaded or associated with it during its lifespan. It provides the entrypoint to acquire a [`Query`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query) object, which sends queries to the database using the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) object’s current database connection, populating result rows into objects that are then stored in the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session), inside a structure called the [Identity Map](http://martinfowler.com/eaaCatalog/identityMap.html) - a data structure that maintains unique copies of each object, where “unique” means “only one object with a particular primary key”.

The [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) begins in an essentially stateless form. Once queries are issued or other objects are persisted with it, it requests a connection resource from an [`Engine`](http://docs.sqlalchemy.org/en/rel_1_1/core/connections.html#sqlalchemy.engine.Engine) that is associated either with the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) itself or with the mapped [`Table`](http://docs.sqlalchemy.org/en/rel_1_1/core/metadata.html#sqlalchemy.schema.Table) objects being operated upon. This connection represents an ongoing transaction, which remains in effect until the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) is instructed to commit or roll back its pending state.

All changes to objects maintained by a [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) are tracked - before the database is queried again or before the current transaction is committed, it **flushes** all pending changes to the database. This is known as the [Unit of Work](http://martinfowler.com/eaaCatalog/unitOfWork.html)pattern.

When using a [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session), it’s important to note that the objects which are associated with it are **proxy objects** to the transaction being held by the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) - there are a variety of events that will cause objects to re-access the database in order to keep synchronized. It is possible to “detach” objects from a [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session), and to continue using them, though this practice has its caveats. It’s intended that usually, you’d re-associate detached objects with another [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) when you want to work with them again, so that they can resume their normal task of representing database state.

大多数通用的场景下，Session 负责建立与数据库会话的通道，并且 Session 在它的生命周期内还维护一个**固有的容器**（holding zone）用来存储所有通过 Session **加载过的对象**以及通过 Session **主动关联的对象**。Session 还为获取 Query 对象提供了入口（session.query），Query 能够通过当前 Session 对应的数据库连接 （db connection） 进行查询，并且把返回的结果集计算到一个个对象中，这些对象最终就存储在 Session 中。 Session 使用身份映射（identity map）技术维护着每个对象的唯一副本，唯一意味着它们都独有自己的主键。

初始化的 Session 是无状态的。一旦通过 Session 发起查询或持久化操作，Session 会从**自身关联的 Engine** 或 它正在执行**操作的 Table** 中请求一个连接。这个连接代表一个持续活动的 transaction，连接会一直保持活动直到 Session 执行 commit 或 rollback 操作。【可以理解为一次 commit 或 rollback 将结束一次事务操作】

```python
def test_session_query():
    session = DBSession()

    tag = session.query(Tag).filter(Tag.id == 20).first()
    print tag.name
    tag.name = 'chang'
    #session.commit()
    session.rollback()  # 回滚上面的修改
    tag = session.query(Tag).filter(Tag.id == 20).first()  # 重新发起事务进行查询
    print tag.name
```

```shell

BEGIN (implicit)
SELECT tag.id AS tag_id, tag.name AS tag_name, tag.atime AS tag_atime 
FROM tag 
WHERE tag.id = %s 
 LIMIT %s
ROLLBACK

BEGIN (implicit)
SELECT tag.id AS tag_id, tag.name AS tag_name, tag.atime AS tag_atime 
FROM tag 
WHERE tag.id = %s 
LIMIT %s

```

Session 会跟踪它关联对象的状态变化，除非显式地重新发起一次查询或当前事务提交了，Session 会 flushes 所有 pending 状态的改变到数据库。这就是 unit of work 模式。

使用 Session 时，有一点需要注意，所有和 Session 关联的对象都相对于 Session 的事务而言都是 proxy objects ，有很多事件会引发对象为了保持同步，重新从数据库获取最新状态。objects 可以从 Session 中 detach，并继续使用，尽管这样做会有不好的一面。detached 对象也可以和另一个 Session 关联，关联之后，它们又可以代表数据库的中数据的状态了。

## Getting a Session

[`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) is a regular Python class which can be directly instantiated. However, to standardize how sessions are configured and acquired, the [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) class is normally used to create a top level [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) configuration which can then be used throughout an application without the need to repeat the configurational arguments.

The usage of [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) is illustrated below:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# an Engine, which the Session will use for connection
# resources
some_engine = create_engine('postgresql://scott:tiger@localhost/')

# create a configured "Session" class
Session = sessionmaker(bind=some_engine)

# create a Session
session = Session()

# work with sess
myobject = MyObject('foo', 'bar')
session.add(myobject)
session.commit()
```

Above, the [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) call creates a factory for us, which we assign to the name `Session`. This factory, when called, will create a new [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) object using the configurational arguments we’ve given the factory. In this case, as is typical, we’ve configured the factory to specify a particular [`Engine`](http://docs.sqlalchemy.org/en/rel_1_1/core/connections.html#sqlalchemy.engine.Engine) for connection resources.

A typical setup will associate the [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) with an [`Engine`](http://docs.sqlalchemy.org/en/rel_1_1/core/connections.html#sqlalchemy.engine.Engine), so that each [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) generated will use this [`Engine`](http://docs.sqlalchemy.org/en/rel_1_1/core/connections.html#sqlalchemy.engine.Engine) to acquire connection resources. This association can be set up as in the example above, using the `bind` argument.

When you write your application, place the [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) factory at the global level. This factory can then be used by the rest of the applcation as the source of new [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) instances, keeping the configuration for how [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) objects are constructed in one place.

The [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) factory can also be used in conjunction with other helpers, which are passed a user-defined [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) that is then maintained by the helper. Some of these helpers are discussed in the section [When do I construct a Session, when do I commit it, and when do I close it?](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_basics.html#session-faq-whentocreate).

Session 本质上是一个可以直接实例化使用的普通 Python 类。为了标准化 Session 的配置和获取工作，sqlalchemy 提供了 sessionmaker。借助 sessionmaker ，Session 的配置可以放置于应用程序的顶层，全局使用。

例子中，sessionmaker 创建了一个工厂 Session，调用这个 Session 将会得到拥有 sessionmaker 配置参数的 Session 对象。在这里，我们配置这个工厂 Session 使用一个特定的 Engine 来获得连接资源。

典型的用法是把 sessionmaker 和一个 Engine 关联，每个新生成的 Session 对象都会通过这个 Engine 获取连接资源，可以通过 sessionmaker 的 bind 参数完成这样的关联。

建议把 sessionmaker 置于 application 的顶层，供全局使用，这样的设计有助于让构造 session 对象的配置始终保持在一处。

sessionmaker  可以用来和其他的 helper 结合使用，传入 helper 一个用户定义的 sessionmaker，这个 sessionmaker 将由这个 helper 维护。

### Adding Additional Configuration to an Existing sessionmaker()

A common scenario is where the [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) is invoked at module import time, however the generation of one or more [`Engine`](http://docs.sqlalchemy.org/en/rel_1_1/core/connections.html#sqlalchemy.engine.Engine) instances to be associated with the [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) has not yet proceeded. For this use case, the [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) construct offers the[`sessionmaker.configure()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker.configure) method, which will place additional configuration directives into an existing [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) that will take place when the construct is invoked:

```python
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# configure Session class with desired options
Session = sessionmaker()

# later, we create the engine
engine = create_engine('postgresql://...')

# associate it with our custom Session class
Session.configure(bind=engine)

# work with the session
session = Session()
```

常见的使用场景是 sessionmaker 在模块的顶层创建，当模块导入时自动调用，有些时候 engine 实例的并没有生成，sessionmaker 提供了 configure 方法来动态的为一个已经存在的 sessionmaker 提供配置



### Creating Ad-Hoc Session Objects with Alternate Arguments

For the use case where an application needs to create a new [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) with special arguments that deviate from what is normally used throughout the application, such as a [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) that binds to an alternate source of connectivity, or a [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) that should have other arguments such as `expire_on_commit` established differently from what most of the application wants, specific arguments can be passed to the [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) factory’s [`sessionmaker.__call__()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker.__call__) method. These arguments will override whatever configurations have already been placed, such as below, where a new [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) is constructed against a specific [`Connection`](http://docs.sqlalchemy.org/en/rel_1_1/core/connections.html#sqlalchemy.engine.Connection):

```
# at the module level, the global sessionmaker,
# bound to a specific Engine
Session = sessionmaker(bind=engine)

# later, some unit of code wants to create a
# Session that is bound to a specific Connection
conn = engine.connect()
session = Session(bind=conn)
```

The typical rationale for the association of a [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) with a specific [`Connection`](http://docs.sqlalchemy.org/en/rel_1_1/core/connections.html#sqlalchemy.engine.Connection) is that of a test fixture that maintains an external transaction - see [Joining a Session into an External Transaction (such as for test suites)](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_transaction.html#session-external-transaction) for an example of this.

某些场合下，我们需要临时更改 session 配置，这些配置和 application 提供的全局 session 不同。为此，sessionmaker.__call__ 方法提供了覆盖全局 session 配置的办法。示例中我们更改了一个 session 的连接。

## Basics of Using a Session

The most basic [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) use patterns are presented here.

### Querying

The [`query()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.query) function takes one or more *entities* and returns a new [`Query`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query) object which will issue mapper queries within the context of this Session. An entity is defined as a mapped class, a [`Mapper`](http://docs.sqlalchemy.org/en/rel_1_1/orm/mapping_api.html#sqlalchemy.orm.mapper.Mapper) object, an orm-enabled *descriptor*, or an `AliasedClass` object:

```
# query from a class
session.query(User).filter_by(name='ed').all()

# query with multiple classes, returns tuples
session.query(User, Address).join('addresses').filter_by(name='ed').all()

# query using orm-enabled descriptors
session.query(User.name, User.fullname).all()

# query from a mapper
user_mapper = class_mapper(User)
session.query(user_mapper)
```

When [`Query`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query) returns results, each object instantiated is stored within the identity map. When a row matches an object which is already present, the same object is returned. In the latter case, whether or not the row is populated onto an existing object depends upon whether the attributes of the instance have been *expired* or not. A default-configured [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) automatically expires all instances along transaction boundaries, so that with a normally isolated transaction, there shouldn’t be any issue of instances representing data which is stale with regards to the current transaction.

The [`Query`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query) object is introduced in great detail in [Object Relational Tutorial](http://docs.sqlalchemy.org/en/rel_1_1/orm/tutorial.html), and further documented inquery_api_toplevel.


用一个或更多个 entities 调用 query function 并返回 query object，query object 将在 当前 session 中执行 query。entity 可以使一个都已经定义好的 mapped class，mapper object，orm-enabled descriptor 或 AliasedClass。

query object 返回结果，实例的对象以 identity map 的形式存储于 session 中。如果 a row 和 session 中已有的的 object 匹配，。是否需要重新 populate row to existing object 取决于实例属性是否 expired。默认的 session 配置会自动让所有实例过期当 transaction 结束。

### Adding New or Existing Items

[`add()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.add) is used to place instances in the session. For *transient* (i.e. brand new) instances, this will have the effect of an INSERT taking place for those instances upon the next flush. For instances which are *persistent* (i.e. were loaded by this session), they are already present and do not need to be added. Instances which are *detached* (i.e. have been removed from a session) may be re-associated with a session using this method:

```
user1 = User(name='user1')
user2 = User(name='user2')
session.add(user1)
session.add(user2)

session.commit()     # write changes to the database
```

To add a list of items to the session at once, use [`add_all()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.add_all):

```
session.add_all([item1, item2, item3])
```

The [`add()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.add) operation **cascades** along the `save-update` cascade. For more details see the section [Cascades](http://docs.sqlalchemy.org/en/rel_1_1/orm/cascades.html#unitofwork-cascades).

add 用来关联一个 object 和 session。transient instance 在 next flush 创建新数据，
persistent instance 没有任何影响，detached instance 又重新加入 session。

### Deleting

The [`delete()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.delete) method places an instance into the Session’s list of objects to be marked as deleted:

```
# mark two objects to be deleted
session.delete(obj1)
session.delete(obj2)

# commit (or flush)
session.commit()
```

#### Deleting from Collections

A common confusion that arises regarding [`delete()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.delete) is when objects which are members of a collection are being deleted. While the collection member is marked for deletion from the database, this does not impact the collection itself in memory until the collection is expired. Below, we illustrate that even after an `Address` object is marked for deletion, it’s still present in the collection associated with the parent `User`, even after a flush:

```
>>> address = user.addresses[1]
>>> session.delete(address)
>>> session.flush()
>>> address in user.addresses
True
```

When the above session is committed, all attributes are expired. The next access of `user.addresses` will re-load the collection, revealing the desired state:

```
>>> session.commit()
>>> address in user.addresses
False
```

The usual practice of deleting items within collections is to forego the usage of [`delete()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.delete) directly, and instead use cascade behavior to automatically invoke the deletion as a result of removing the object from the parent collection. The `delete-orphan` cascade accomplishes this, as illustrated in the example below:

```
mapper(User, users_table, properties={
    'addresses':relationship(Address, cascade="all, delete, delete-orphan")
})
del user.addresses[1]
session.flush()
```

Where above, upon removing the `Address` object from the `User.addresses` collection, the `delete-orphan`cascade has the effect of marking the `Address` object for deletion in the same way as passing it to [`delete()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.delete).

See also [Cascades](http://docs.sqlalchemy.org/en/rel_1_1/orm/cascades.html#unitofwork-cascades) for detail on cascades.

#### Deleting based on Filter Criterion

The caveat with `Session.delete()` is that you need to have an object handy already in order to delete. The Query includes a [`delete()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query.delete) method which deletes based on filtering criteria:

```
session.query(User).filter(User.id==7).delete()
```

The `Query.delete()` method includes functionality to “expire” objects already in the session which match the criteria. However it does have some caveats, including that “delete” and “delete-orphan” cascades won’t be fully expressed for collections which are already loaded. See the API docs for [`delete()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query.delete) for more details.


delete 用来标记 session 中对象为 deleted。

如果 delete 的是一个 collection 中的成员，默认行为下，集合中的成员并不会被标记为 deleted，直到 collection expired。

从 collection 中删除一个成员更普遍的做法是使用级联操作，当成员删除是，自动删除删除成员对于的 row。

使用 session 的 delete 的限制条件是被删除的 object 一定在当前的上下文中存在，query 的 delete 不存在这样的限制。




### Flushing

When the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) is used with its default configuration, the flush step is nearly always done transparently. Specifically, the flush occurs before any individual [`Query`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query) is issued, as well as within the [`commit()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.commit) call before the transaction is committed. It also occurs before a SAVEPOINT is issued when [`begin_nested()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.begin_nested) is used.

Regardless of the autoflush setting, a flush can always be forced by issuing [`flush()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.flush):

```
session.flush()
```

The “flush-on-Query” aspect of the behavior can be disabled by constructing [`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) with the flag `autoflush=False`:

```
Session = sessionmaker(autoflush=False)
```

Additionally, autoflush can be temporarily disabled by setting the `autoflush` flag at any time:

```
mysession = Session()
mysession.autoflush = False
```

Some autoflush-disable recipes are available at [DisableAutoFlush](http://www.sqlalchemy.org/trac/wiki/UsageRecipes/DisableAutoflush).

The flush process *always* occurs within a transaction, even if the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) has been configured with`autocommit=True`, a setting that disables the session’s persistent transactional state. If no transaction is present, [`flush()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.flush) creates its own transaction and commits it. Any failures during flush will always result in a rollback of whatever transaction is present. If the Session is not in `autocommit=True` mode, an explicit call to [`rollback()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.rollback) is required after a flush fails, even though the underlying transaction will have been rolled back already - this is so that the overall nesting pattern of so-called “subtransactions” is consistently maintained.


默认配置下，用户感知不到 flush 的执行。何时会有flush？query 执行前，commit 执行前，在begin_nest 中 savepoint 执行前。

不管默认配置如何，任何时候都可以强制进行 flush。

执行 query 时默认执行 flush 的行为可以在 sessionmaker 中更改，除此之外，在 session 生命周期的任何时间都可以禁止 autoflush 操作。

**flush 执行失败会导致其所在的 transaction 发生 rollback，即使在 autocommit=True 模式下，flush 失败后必须要显示调用 rollback，即使底层的 transaction 已经 rollback**

### Committing

[`commit()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.commit) is used to commit the current transaction. It always issues [`flush()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.flush) beforehand to flush any remaining state to the database; this is independent of the “autoflush” setting. If no transaction is present, it raises an error. Note that the default behavior of the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) is that a “transaction” is always present; this behavior can be disabled by setting `autocommit=True`. In autocommit mode, a transaction can be initiated by calling the [`begin()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.begin) method.

Note

The term “transaction” here refers to a transactional construct within the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) itself which may be maintaining zero or more actual database (DBAPI) transactions. An individual DBAPI connection begins participation in the “transaction” as it is first used to execute a SQL statement, then remains present until the session-level “transaction” is completed. See [Managing Transactions](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_transaction.html#unitofwork-transaction) for further detail.

Another behavior of [`commit()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.commit) is that by default it expires the state of all instances present after the commit is complete. This is so that when the instances are next accessed, either through attribute access or by them being present in a [`Query`](http://docs.sqlalchemy.org/en/rel_1_1/orm/query.html#sqlalchemy.orm.query.Query) result set, they receive the most recent state. To disable this behavior, configure[`sessionmaker`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.sessionmaker) with `expire_on_commit=False`.

Normally, instances loaded into the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) are never changed by subsequent queries; the assumption is that the current transaction is isolated so the state most recently loaded is correct as long as the transaction continues. Setting `autocommit=True` works against this model to some degree since the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) behaves in exactly the same way with regard to attribute state, except no transaction is present.

commit 之前一定会调用 flush，这个执行和 autoflush 的配置是相互独立不影响的。如果没有事务存在，则抛出错误。session 的默认行为就是一个 transaction 总是存在。可以用 autocommit=True 来改变，在 autocommit mode 下，必须显示调用 begin 来开启事务。

session 的事务是在 session 内部维持的0个或多个数据库事务。一个独立的 DBAPI 一旦开始执行 sql 语句就代表参与到 session 的事务，直到session 的事务结束为止。一个独立的 DBAPI 一旦开始执行 sql 语句就代表参与到 session 的事务，直到session 的事务结束为止。。

commit 之后会导致当前实例的状态 expired，直到下一次查询载入新的实例。可以通过 expire_on_commit 来禁止这种行为。

### Rolling Back

[`rollback()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.rollback) rolls back the current transaction. With a default configured session, the post-rollback state of the session is as follows:

> - All transactions are rolled back and all connections returned to the connection pool, unless the Session was bound directly to a Connection, in which case the connection is still maintained (but still rolled back).
> - Objects which were initially in the *pending* state when they were added to the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) within the lifespan of the transaction are expunged, corresponding to their INSERT statement being rolled back. The state of their attributes remains unchanged.
> - Objects which were marked as *deleted* within the lifespan of the transaction are promoted back to the *persistent* state, corresponding to their DELETE statement being rolled back. Note that if those objects were first *pending* within the transaction, that operation takes precedence instead.
> - All objects not expunged are fully expired.

With that state understood, the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session) may safely continue usage after a rollback occurs.

When a [`flush()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.flush) fails, typically for reasons like primary key, foreign key, or “not nullable” constraint violations, a [`rollback()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.rollback) is issued automatically (it’s currently not possible for a flush to continue after a partial failure). However, the flush process always uses its own transactional demarcator called a *subtransaction*, which is described more fully in the docstrings for [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session). What it means here is that even though the database transaction has been rolled back, the end user must still issue [`rollback()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.rollback) to fully reset the state of the [`Session`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session).

所有事务都回滚，所有的 connection return to pool，如果有 session 直接绑定了一个连接，这个连接会保持。

pending state 状态 object expunged，insert 语句回滚，属性状态维持原样。

deleted state 变成 persistent state，delete 语句回滚。

flush 失败，就会发生 rollback。即使 db transaction 已经回滚，rollback 还是需要在应用程序中显式调用。

### Closing

The [`close()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.close) method issues a [`expunge_all()`](http://docs.sqlalchemy.org/en/rel_1_1/orm/session_api.html#sqlalchemy.orm.session.Session.expunge_all), and [releases](http://docs.sqlalchemy.org/en/rel_1_1/glossary.html#term-releases) any transactional/connection resources. When connections are returned to the connection pool, transactional state is rolled back as well.

释放所有事务，连接。
