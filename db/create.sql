SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

CREATE SCHEMA IF NOT EXISTS `hispar` DEFAULT CHARACTER SET latin1 ;
USE `hispar` ;

-- -----------------------------------------------------
-- Table `hispar`.`route`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `hispar`.`route` (
  `idroute` INT(11) NOT NULL AUTO_INCREMENT ,
  `AS` VARCHAR(45) NOT NULL ,
  `subnet` VARCHAR(18) NULL DEFAULT NULL ,
  `HRange` CHAR(5) NOT NULL ,
  `cost` INT(11) NULL DEFAULT NULL ,
  PRIMARY KEY (`idroute`) )
ENGINE = InnoDB
AUTO_INCREMENT = 10
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `hispar`.`quality`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `hispar`.`quality` (
  `route_id` INT(11) NOT NULL ,
  `hour_of_day` INT(11) NOT NULL ,
  `m_time` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP ,
  `latency` FLOAT NULL DEFAULT NULL ,
  `jitter` FLOAT NULL DEFAULT NULL ,
  `loss` FLOAT NULL DEFAULT NULL ,
  `subnet` VARCHAR(18) NULL DEFAULT NULL ,
  PRIMARY KEY (`route_id`, `hour_of_day`, `m_time`) ,
  INDEX `fk_quality_route` (`route_id` ASC) ,
  INDEX `index_hod` (`hour_of_day` ASC) ,
  CONSTRAINT `fk_quality_route0`
    FOREIGN KEY (`route_id` )
    REFERENCES `hispar`.`route` (`idroute` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `hispar`.`quality_daily`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `hispar`.`quality_daily` (
  `route_id` INT(11) NOT NULL ,
  `hour_of_day` INT(11) NOT NULL ,
  `m_date` DATE NOT NULL ,
  `avg_latency` FLOAT NOT NULL ,
  `avg_jitter` FLOAT NOT NULL ,
  `avg_loss` FLOAT NOT NULL ,
  `m_count` INT(11) NOT NULL ,
  PRIMARY KEY (`route_id`, `hour_of_day`, `m_date`) ,
  INDEX `fk_quality_route` (`route_id` ASC) ,
  INDEX `index_hod` (`hour_of_day` ASC) ,
  INDEX `index_date` (`m_date` ASC) ,
  CONSTRAINT `fk_quality_route`
    FOREIGN KEY (`route_id` )
    REFERENCES `hispar`.`route` (`idroute` )
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;


-- -----------------------------------------------------
-- Table `hispar`.`traffic`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `hispar`.`traffic` (
  `idtraffic` INT(11) NOT NULL AUTO_INCREMENT ,
  `AS` VARCHAR(45) NOT NULL ,
  `ip` VARCHAR(15) NOT NULL ,
  `count` INT(11) NOT NULL DEFAULT '0' ,
  PRIMARY KEY (`idtraffic`) )
ENGINE = InnoDB
DEFAULT CHARACTER SET = latin1;

USE `hispar` ;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
