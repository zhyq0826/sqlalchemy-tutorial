### 问题

#### sqlalchemy 是什么？

Python SQL tookit and ORM

#### sqlalchemy 能够做什么？

在任意的 Python Application 中以 Pythonic 的方式使用 sql database，还提供 ROM，管理复杂的表关系和依赖

#### sqlalchemy 的特性是什么？

http://www.sqlalchemy.org/features.html

###### **No ORM Required**

ORM 不是必须的。 

sqlalchemy 包含两部分独立的组件: core 和 ORM。core 层本质就是提供各种特性的 SQL 抽象工具集，包含有
- 包含对 python DBAPI 的抽象实现和各种行为实现
- 允许使用 Python 来完成任意复杂 SQL 语言的 SQL 表达式语言系统 
- schema 表达系统，不但可以消除对 DDL 数据库定义语言的依赖，也可以对已有 db 系统进行反射内省
- 可以允许任意 Python 对象映射为数据库对象的类型系统

ORM 就是构建于 core 之上的一个可选 package

###### **Mature, High Performing Architecture**

成熟高性能的架构

###### **DBA Approved**

是对 DBA 友好的，提供生成 SQL 语句的功能，而且经过全面优化，完全的事物支持和批量写入支持，支持对象之间的实体引用

###### **unit of work**

The Unit Of Work system， 集中式的对象映射系统，实现对 insert、update、delete 操作进行队列式管理，批量写入。这样的实现，最大程度的提升了效率，并且保证事务是安全的，而且把死锁发生的几率降到最低。

[Fowler's "Unit of Work" pattern](http://martinfowler.com/eaaCatalog/unitOfWork.html)

###### **Function-based query construction**

基于函数的查询构建语言，允许 SQL 语句构建在 Python 的函数和表达式之上，包含

The full range of what's possible includes boolean expressions, operators, functions, table aliases, selectable subqueries, insert/update/delete statements, correlated updates, selects, and EXISTS clauses, UNION clauses, inner and outer joins, bind parameters, and free mixing of literal text within expressions。

###### **Modular and Extensible**

模块化和可扩展的。

sqlalchemy 的不同部分都可以单独使用而不互相影响，比如 connect pooling，SQL statement compilation，transactionl service 都可以独立使用而不相互依赖，而且他们还可以通过各种 plugin points 进行扩展。

内部集成的事件系统可以把自定义代码注入到调用会话多达50处，包含

core statement execution，schema generation and introspection，connection pool operation，object relation configuration，persistence operations，attribute mutation events, and transactional stages。

新的 SQL 语句和 SQL 类型也可以无缝的集成。

###### **Separate mapping and class design**

类的定义和映射是完全分开的。虽然 ORM 提供了使用 class 的方式来映射 table metadata，但是这种方式是完全可选的，ORM 认为 class 和 class mapping 的 table metata 是完全独立的。通过 mapper 函数，任意的 Python class 都可以映射 到 table 和 视图

###### **Eager-loading and caching of related objects and collections**

支持热加载，关系对象缓存

###### **Pre- and post-processing of data**

支持预处理和后处理数据

###### **Raw SQL statement mapping**

支持纯 SQL 语句的执行，并且返回的结果集可以像 ORM 一样，以对象的方式存取。

SQLA's object relational query facilities can accommodate raw SQL statements as well as plain result sets, and object instances can be generated from these results in the same manner as any other ORM operation 

#### sqlalchemy 特性决定了它能够做什么，使用场景在哪里？

需要关系型数据库交互的各种应用

#### 如果要在实际项目中使用 sqlalchemy ，需要关注的重点是什么(现在的和将来的)？

在大项目中使用 sqlalchemy 必需要能做到：

- 代码容易维护：容易读懂理解和方便修改
- 组织架构方面容易扩展：新增功能或替换功能改动不大
- 当代码量变大，业务变复杂，代码的组织性依然良好，业务代码的可读性依然良好
- 在用户基数小的初期性能可接受，用户基数大的时候不满足性能的地方方便替换和更改

#### sqlalchemy 的特性是否能满足关注的这些点，为什么？

1. sqlalchemy 提供了可选的 ORM，对于简单的增删改查，可选的 ORM 完全满足实际业务，开发效率高
2. 如果业务非常复杂，代码量非常多，数据库表的关系控制可以选择**不**交给 sqlalchemy 处理，把对业务的控制权放到开发手中，这样不容易失控
3. sqlalchemy 提供的表映射是无关数据库的，除非使用了特定数据库的方言，否则很容易实现底层数据库的迁移和替换
4. 提供纯 sql 语句的执行，使用 session 来统一管理事务，既可以满足一般性业务，面对复杂业务也能应对

#### sqlalchemy 的组织架构是如何的，由哪些关键的组件组成，每个关键组件的承担的功能和责任是什么，各个组件的相互关系是什么？

http://aosabook.org/en/sqlalchemy.html

### 关键特性

#### 理解 session

session 是应用程序和 database 交互的通道，通过 session 应用程序可以向 database 发起查询、更新数据、删除数据、开启事务、提交事务等。

任意的 ORM 对象都可以通过 session 和 database 关联，session 负责对这些关联的对象提供更新、查询、删除等操作。

**session lifespan**

- session 初次构建，没有和任何对象关联
- session 发起 query 操作，返回的结果集和 session 相关连
- 新对象加入 session 之后和 session 发生关联，此时这些对象并没有被持久化
- 调用 commit 持久化 session 中发生变化的对象，包括新增的和对象属性发生改变的对象
- 关闭 session

**session actions**

- add 对象和 session 发生关联
- delete 取消对象和 session 的关联
- flush 
- commit 持久化对象的更改到数据库
- close 关闭当前 session 

**session objects state**

- Transient: an instance that's not included in a session and has not been persisted to the database.
- Pending: an instance that has been added to a session but not persisted to a database yet. It will be persisted to the database in the next session.commit().
- Persistent: an instance that has been persisted to the database and also included in a session. You can make a model object persistent by committing it to the database or query it from the database.
- Detached: an instance that has been persisted to the database but not included in any sessions.

**session objects unique associate**


一个对象在任意时刻只能和一个 session 关联

```python

>>> jessica = User(name='Jessica')
>>> s1.add(jessica)
>>> s2.add(jessica)
Traceback (most recent call last):
......
sqlalchemy.exc.InvalidRequestError: Object '' is already attached to session '2' (this is '3')
   
```
